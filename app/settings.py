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

"""Settings to override default settings."""

import logging
import os

#
# Override settings
#
DEBUG = True

HTTP_PORT = int(os.environ.get('PORT', 3333))
HTTP_ADDRESS = os.environ.get('HOST', '0.0.0.0')

REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_DB = int(os.environ.get('REDIS_DB', 0))

DEFAULT_LL = 'ERROR'
LOG_LEVEL = os.environ.get('LOG_LEVEL', DEFAULT_LL)

#
# Set logging level
#

try:
    logging.getLogger().setLevel(LOG_LEVEL)
except Exception:
    logging.getLogger().setLevel(DEFAULT_LL)

JOB_CLASS_PACKAGES = ['app']
STATIC_DIR_PATH = './static'
TEMPLATE_DIR_PATH = './static'

BASIC_AUTH_CONFIG = {
    'user': os.environ.get('USERNAME', ''),
    'pass': os.environ.get('PASSWORD', ''),
    'realm': os.environ.get('REALM', 'Aether Scheduler')
}

REQUIRES_AUTH = bool(os.environ.get('REQUIRES_AUTH', False))
APP_PREFIX = os.environ.get('APP_PREFIX', None)
