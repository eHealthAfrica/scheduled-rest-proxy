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


import collections
from datetime import datetime
from uuid import uuid4


class CallableDict(collections.UserDict):
    # CD allow for functions stored in a dictionary
    # to be evaluated at GET time. This is useful for
    # providing functions at JSONPathes

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if callable(value):
            return value()
        else:
            return value


def __iso_now():
    return datetime.now().isoformat()


def __uuid_str():
    return str(uuid4())


def replace_nested(_dict, keys, value):
    # recursively puts a value deep into a dictionary at path [k1.k2.kn]
    if len(keys) > 1:
        try:
            _dict[keys[0]] = replace_nested(_dict[keys[0]], keys[1:], value)
        except KeyError:  # Level doesn't exist yet
            _dict[keys[0]] = replace_nested({}, keys[1:], value)
    else:
        _dict[keys[0]] = value
    return _dict


BUILTINS = CallableDict({
    'now': __iso_now,
    'uuid': __uuid_str
})
