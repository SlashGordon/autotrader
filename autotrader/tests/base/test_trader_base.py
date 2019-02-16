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
import unittest
import os
from autotrader.base.trader_base import TraderBase


class TestTraderBase(unittest.TestCase):
    """
    Test for trader basis methods
    """

    @staticmethod
    def test_logger():
        """
        tests the logger creation
        :return: nothing
        """
        logger = TraderBase.setup_logger("auto_trader")
        assert logger is not None
        logger = TraderBase.setup_logger(None)
        assert logger is not None

    @staticmethod
    def test_config():
        """
        tests the config creation by environment variable and root project dir
        :return: nothing
        """
        # test with config.ini in project root
        main_config = TraderBase.get_config()
        assert main_config is not None
        # test with environment variable
        file_config = open('config_test_unittest.ini', 'wt', encoding='utf-8')
        test_value = "[test]\ntest_value = 123456"
        file_config.write(test_value)
        file_config.close()
        old_config_path = os.environ["CONFIG_FILE"]
        os.environ["CONFIG_FILE"] = "config_test_unittest.ini"
        main_config = TraderBase.get_config()
        assert main_config['test']['test_value'] == '123456'
        os.environ.pop("CONFIG_FILE")
        os.environ["CONFIG_FILE"] = old_config_path


if __name__ == '__main__':
    unittest.main()
