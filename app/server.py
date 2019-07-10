#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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

import base64
import os

import tornado

# needed by scheduler
os.environ['NDSCHEDULER_SETTINGS_MODULE'] = 'app.settings'  # noqa

import re

from ndscheduler.server.server import SchedulerServer  # noqa
from ndscheduler import settings  # noqa
from ndscheduler.core import scheduler_manager
from ndscheduler.server.handlers import audit_logs
from ndscheduler.server.handlers import executions
from ndscheduler.server.handlers import index
from ndscheduler.server.handlers import jobs

from .settings import APP_PREFIX


class UnAuthenticatedServer(SchedulerServer):

    def __init__(self, scheduler_instance):
        super(UnAuthenticatedServer, self).__init__()
        if APP_PREFIX:
            for handler in self.application.handlers[0][1]:
                handler.regex = re.compile(
                    handler.regex.pattern.replace('/', f'/{APP_PREFIX}/', 1)
                )


class AuthenticatedServer(SchedulerServer):

    def __init__(self, scheduler_instance):
        # Start scheduler
        self.scheduler_manager = scheduler_instance

        self.tornado_settings = dict(
            debug=settings.DEBUG,
            static_path=settings.STATIC_DIR_PATH,
            template_path=settings.TEMPLATE_DIR_PATH,
            scheduler_manager=self.scheduler_manager
        )

        # Setup server
        URLS = [
            # Index page
            (r'/', require_basic_auth(index.Handler, settings.BASIC_AUTH_CONFIG)),

            # APIs
            (r'/api/%s/jobs' % self.VERSION, require_basic_auth(jobs.Handler, settings.BASIC_AUTH_CONFIG)),
            (r'/api/%s/jobs/(.*)' % self.VERSION, require_basic_auth(jobs.Handler, settings.BASIC_AUTH_CONFIG)),
            (r'/api/%s/executions' % self.VERSION, require_basic_auth(executions.Handler, settings.BASIC_AUTH_CONFIG)),
            (r'/api/%s/executions/(.*)' % self.VERSION, require_basic_auth(executions.Handler, settings.BASIC_AUTH_CONFIG)),
            (r'/api/%s/logs' % self.VERSION, require_basic_auth(audit_logs.Handler, settings.BASIC_AUTH_CONFIG)),
        ]
        self.application = tornado.web.Application(URLS, **self.tornado_settings)
        if APP_PREFIX:
            for handler in self.application.handlers[0][1]:
                handler.regex = re.compile(
                    handler.regex.pattern.replace('/', f'/{APP_PREFIX}/', 1)
                )


# Taken from unmerged PR#18 in NDScheduler
def require_basic_auth(handler_class, config=None):
    config = config or dict()
    config.setdefault('user', '')
    config.setdefault('pass', '')
    config.setdefault('realm', 'Next Scheduler')

    if config['user'] and config['pass']:
        def wrap_execute(handler_execute):
            def check_auth(handler):
                auth_header = handler.request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Basic '):
                    bytes_header = auth_header.encode('utf-8')
                    auth_decoded = base64.decodestring(bytes_header[6:]).decode('utf-8')
                    if f'{config["user"]}:{config["pass"]}' == str(auth_decoded):
                        return True
                handler.set_status(401)
                handler.set_header('WWW-Authenticate', 'Basic realm=%s' % config['realm'])
                handler._transforms = []
                handler.finish()
                return False

            def _execute(self, transforms, *args, **kwargs):
                if not check_auth(self):
                    return False
                return handler_execute(self, transforms, *args, **kwargs)
            return _execute

        handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class
