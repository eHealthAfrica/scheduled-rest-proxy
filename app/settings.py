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

#
# Set logging level
#
logging.getLogger().setLevel(logging.DEBUG)

JOB_CLASS_PACKAGES = ['app']
STATIC_DIR_PATH = './static'
TEMPLATE_DIR_PATH = './static'

BASIC_AUTH_CONFIG = {
    'user': os.environ.get('USERNAME', ''),
    'pass': os.environ.get('PASSWORD', ''),
    'realm': os.environ.get('REALM', 'Aether Scheduler')
}

print(BASIC_AUTH_CONFIG)