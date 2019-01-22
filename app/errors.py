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

from .logger import LOG


class ReportableError(Exception):
    pass


class Aggregator(object):

    def __init__(self):
        self.errors = {}

    def report_ok(self, _id):
        self.report(_id, "Successfully Handled")

    def report(self, _id, exc):
        exc = str(exc)
        LOG.debug(f'{_id} reports {exc}')
        existing = self.errors.get(_id, {})
        count = existing.get(exc, 0)
        count += 1
        existing[exc] = count
        self.errors[_id] = existing

    def read(self, _id):
        try:
            return self.errors[_id]
        except KeyError:
            return []

    def destructive_read(self, _id):
        res = dict(self.read(_id))
        try:
            del self.errors[_id]
        except KeyError:
            pass
        return res


ERR = Aggregator()
