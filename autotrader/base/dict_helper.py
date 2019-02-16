# -*- coding: utf-8 -*-
""" Autotrader

 Copyright 2017-2018 Slash Gordon

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""


class DictHelper:
    """
    Little helper class for request operations
    """
    @staticmethod
    def find_key(key, var, conditions=[]):
        """
        Find all keys in nested dicts
        :param key:
        :param var:
        :param conditions: list of tuple(key value pair).
         Result will be returned when dict contains condition.
        :return:
        """
        if hasattr(var, 'items'):
            for k, v in var.items():
                if k == key and DictHelper.__is_result(conditions, var):
                    yield v
                elif type(v) is dict:
                    for result in DictHelper.find_key(key, v, conditions):
                        if DictHelper.__is_result(conditions, v):
                            yield result
                elif type(v) is list:
                    for d in v:
                        for result in DictHelper.find_key(key, d, conditions):
                            yield result
        elif type(var) is list:
            for items in var:
                for result in DictHelper.find_key(key, items, conditions):
                    yield result

    @staticmethod
    def find_first_key(key, var):
        """
        Find first keys in nested dicts
        :param key:
        :param var:
        :return:
        """
        my_values = [x for x in DictHelper.find_key(key, var)]
        if my_values:
            return my_values[0]
        return None

    @staticmethod
    def __is_result(conditions, mydict):
        for condition in conditions:
            if not (condition[0] in mydict and mydict[condition[0]] == condition[1]):
                return False
        return True
