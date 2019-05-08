#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import redis
import requests
from requests.auth import HTTPBasicAuth

from .errors import ReportableError, ERR
from .logger import LOG
from .jsonpath import CachedParser
from .settings import REDIS_HOST, REDIS_PORT, REDIS_DB
from .utils import BUILTINS, replace_nested

SCHEMA = {}
with open('schema.json') as f:
    SCHEMA = json.load(f)

# State persistence between job runs

REDIS = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    encoding="utf-8",
    decode_responses=True
)


def load_from_datastore(job_id):
    if REDIS.exists(job_id):
        return json.loads(REDIS.get(job_id))
    LOG.debug(f'No matching job {job_id} in Redis.')
    return {}


def save_to_datestore(job_id, obj):
    LOG.info(f'putting {obj} into {job_id}')
    REDIS.set(job_id, json.dumps(obj))


DATAMAP_PARTS = [
    'headers',
    'query_params',
    'json_body',
    'form_body',
    'save_resource'
]


REST_CALLS = {  # Available calls mirrored in json schema
    "HEAD": requests.head,
    "GET": requests.get,
    "POST": requests.post,
    "PUT": requests.put,
    "DELETE": requests.delete,
    "OPTIONS": requests.options
}


def handle_request_problems(_id, req):
    if not req.status_code < 300:
        ERR.report(_id, ReportableError(f'{req.status_code} : {req.text}'))
        raise ReportableError()
    try:
        res = req.json()
        LOG.debug(f'response: {res}')
        return res
    except Exception:
        try:
            LOG.error(f'Non json response: {req.text}')
            ERR.report(_id, ReportableError(
                f'Source API does not return JSON: {req.text}'))
        except Exception:
            LOG.error(f'Could not report non-json response')
            ERR.report(_id, ReportableError(
                'Source API does not return JSON: no-text'))
        raise ReportableError()


def data_from_datamap(datamap, requirements):
    # Grab requirements in keys from datamap
    data = {}
    for key in requirements.keys():
        if len(key.split('.')) > 1:
            # upsert output
            data = replace_nested(data, key.split('.'), datamap.get(key))
        else:
            # Try to merge two dictionaries
            existing = data.get(key, {})
            value = datamap.get(key, {})
            if isinstance(value, dict) and isinstance(existing, dict):
                data[key] = {**existing, **value}
            else:
                # take value from datamap
                data[key] = value
    return data


def map_data(config, raw_data):
    # generate a datamap from a set of raw data and an instruction set
    data_map = {}
    requirements = {}
    for part in DATAMAP_PARTS:
        requirements.update(config.get(part, {}))
    for key, path in requirements.items():
        matches = CachedParser.find(path, raw_data)
        if not matches:
            continue
        if len(matches) > 1:
            data_map[key] = [m.value for m in matches]
        else:
            data_map[key] = matches[0].value
    return data_map


def filter_config(config, target_prefix):
    return {
        k.replace(target_prefix, ''): v
        for k, v in config.items()
        if target_prefix in k
    }


def do_request(_id, config, mapped_data, override_url=None):
    url = config['url']
    try:
        if not override_url:
            full_url = url.format(**mapped_data)
        else:
            full_url = override_url
    except KeyError as ker:
        # self comes from parent class?
        LOG.error(f'Error sending message in job {_id}: {ker}' +
                  f'{url} -> {mapped_data}')
        raise requests.URLRequired(f'bad argument in URL: {ker}')
    fn = REST_CALLS[config['type'].upper()]
    auth = config.get('basic_auth')
    if auth:
        auth = HTTPBasicAuth(auth['user'], auth['password'])
    params = config.get('query_params')
    if params and not override_url:
        params = data_from_datamap(mapped_data, params)
    else:
        params = None
    form_body = config.get('form_body')
    if form_body:
        form_body = data_from_datamap(mapped_data, config.get('form_body'))
    json_body = config.get('json_body')
    if json_body:
        json_body = data_from_datamap(mapped_data, json_body)
    token = config.get('token', {})
    if token:
        token = {'Authorization': f'access_token {token}'}
    headers = config.get('headers', {})
    if headers:
        headers = data_from_datamap(mapped_data, headers)
    headers = {**token, **headers}  # merge in token if we have one
    request_kwargs = {
        'auth': auth,
        'headers': headers,
        'params': params,
        'json': json_body,
        'data': form_body
    }
    if not config.get('mock_request', False):
        return fn(
            full_url,
            **request_kwargs
        )
    request_kwargs['full_url'] = full_url
    LOG.debug(request_kwargs)
    ERR.report(_id, json.dumps(request_kwargs))
    raise ReportableError()


def handle_job(config, *args, **kwargs):
    try:
        validate(config, SCHEMA)
        LOG.debug('Job config is valid.')
    except ValidationError as ver:
        LOG.error(ver)
        raise ValidationError('Job Configuration was not valid')
    _id = config['id']
    try:
        source = get_source(config)
    except ReportableError:
        return ERR.destructive_read(_id)
    process_response(config, source)
    return ERR.destructive_read(_id)


def get_source(config, override_url=None):
    job_id = config['id']
    # get state from datastore
    resources = load_from_datastore(job_id)
    if not resources:
        resources = config.get('initial_query_resources', {})
    else:
        LOG.debug(f'Job {job_id} got resources: {resources}')
    resources['_builtins'] = dict(BUILTINS)  # Freeze a copy
    raw_data = {
        'resource': resources,
        'constants': config.get('constants', {})
    }
    source_config = filter_config(config, 'source_')
    mapped_data = map_data(source_config, raw_data)
    source = do_request(
        job_id,
        source_config,
        mapped_data,
        override_url=override_url
    )
    return handle_request_problems(job_id, source)


def process_response(config, source):
    # get results
    job_id = config['id']
    query_resource = config.get('query_resource', None)
    dest_config = filter_config(config, 'dest_')
    constants = config.get('constants', {})  # optional
    results_path = config['source_msg_path']
    matches = CachedParser.find(results_path, source)
    rows = [m.value for m in matches]
    for row in rows:
        send_to_destination(job_id, dest_config,
                            constants, query_resource, row)
    # detect pagination
    paged = config.get('source_pagination_url', None)
    if paged:
        matches = CachedParser.find(paged, source)
        try:
            override_url = [m.value for m in matches][0]
            if not override_url:
                return
        except IndexError:
            return
        new_source = get_source(config, override_url=override_url)
        return process_response(config, new_source)


def send_to_destination(job_id, dest_config, constants, query_resource, row):
    # get state from datastore
    resources = load_from_datastore(job_id)
    resources['_builtins'] = dict(BUILTINS)  # frozen values
    # process message
    raw_data = {
        'msg': row,
        'resource': resources,
        'constants': constants
    }
    # send data to destination
    mapped_data = map_data(dest_config, raw_data)
    try:
        req = do_request(job_id, dest_config, mapped_data)
        if req:
            handle_request_problems(job_id, req)
    except ReportableError:
        return  # Don't change resources on failure
    ERR.report_ok(job_id)
    resources = data_from_datamap(mapped_data, query_resource)
    save_to_datestore(job_id, resources)
