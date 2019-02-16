#!/usr/bin/env python
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

from setuptools import setup, find_packages
EXCLUDE_FROM_PACKAGES = ['autotrader.bin*',
                         'autotrader.tests*',
                         'autotrader.test_data*',
                         'autotrader.datasource.database.migrate*']


def get_requirements(requirements):
    with open(requirements) as requirement_file:
        content = requirement_file.readlines()
    content = [x.strip() for x in content]
    return content

setup(
    name='autotrader',
    version='0.0.0',
    description='Python Algorithmic Trading',
    py_modules=['autotrader'],
    author='Slash Gordon',
    author_email='slash.gordon.dev@gmail.com',
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    entry_points={'console_scripts': [
            'autotrader = autotrader.base.command_line:autotrader_app',
    ]},
    zip_safe=True,
    install_requires=get_requirements('requirements.txt'),
)
