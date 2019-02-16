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
import logging
from autotrader.datasource.yahoo_finance_client import YahooFinanceClient

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestYahooClient(unittest.TestCase):
    """ Test class for yahoo client.
    The client is at moment only used for index data collection.
    """

    @staticmethod
    def test_cookie_and_indices():
        """
        Test if cookie detection and index data collection works.
        :return: nothing
        """
        yah = YahooFinanceClient(TEST_LOGGER)
        assert yah.set_crumb()
        indices = ['DAX', 'MDAX', 'SDAX', 'CDAX', 'TECDAX']
        for index in indices:
            bars = yah.get_series(index, 'P30D')
            assert bars is not None and bars


if __name__ == '__main__':
    unittest.main()
