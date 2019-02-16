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
import datetime
import unittest
import logging
import numpy.testing as npt
from autotrader.base.trader_base import TraderBase
from autotrader.filter.adx_filter import AdxFilter as Adx
from autotrader.filter.rsi_filter import RsiFilter as Rsi
from autotrader.datasource.database.stock_database import StockDataBase as Db
from autotrader.datasource.database.stock_schema import Stock, BARS_NUMPY

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestStrengthFilter(unittest.TestCase):
    """
    Tests all strength filters
    """

    @classmethod
    def setUpClass(cls):
        cls.config = TraderBase.get_config()
        cls.db_tool = Db(cls.config['sql'], TEST_LOGGER)
        cls.db_tool.connect()

    @classmethod
    def tearDownClass(cls):
        cls.db_tool.close()
        pass

    def tearDown(self):
        pass

    def setUp(self):
        pass

    def test_adx(self):
        """
        Tests adx with two stocks with freezed data set
        """
        symbols = [["LHA", 46.9888, 1], ["MRK", 21.4104, 0]]
        for symbol in symbols:
            stock = self.db_tool.session.query(Stock).filter(symbol[0] == Stock.symbol).first()
            arguments = {
                'stock': stock,
                'name': 'AdxFilterP14',
                'bars': stock.get_bars(
                    start=datetime.datetime(2017, 8, 1, 0, 0),
                    end=datetime.datetime(2017, 10, 1, 0, 0),
                    output_type=BARS_NUMPY),
                'threshold_buy': 30,
                'threshold_sell': 30,
                'parameter': 23,
                'lookback': 1
            }
            my_filter = Adx(arguments, TEST_LOGGER)
            self.assertRaises(RuntimeError, my_filter.analyse)
            arguments["parameter"] = 14
            my_filter = Adx(arguments, TEST_LOGGER)
            status = my_filter.analyse()
            TEST_LOGGER.info("%s score is: %s and status %s", symbol[0],
                             my_filter.get_calculation(), status)
            npt.assert_almost_equal(my_filter.get_calculation(), symbol[1], decimal=4)
            assert symbol[2] == status

    def test_rsi(self):
        """
        Tests adx with two stocks with freezed data set
        """
        symbols = [["LHA", 75.3008, 1], ["MRK", 58.7625, 0]]
        for symbol in symbols:
            stock = self.db_tool.session.query(Stock).filter(
                symbol[0] == Stock.symbol).first()
            arguments = {
                'stock': stock,
                'name': 'AdxFilterP14',
                'bars': stock.get_bars(
                    start=datetime.datetime(2017, 8, 1, 0, 0),
                    end=datetime.datetime(2017, 10, 1, 0, 0),
                    output_type=BARS_NUMPY),
                'threshold_buy': 70,
                'threshold_sell': 70,
                'parameter': 44,
                'lookback': 1
            }
            my_filter = Rsi(arguments, TEST_LOGGER)
            self.assertRaises(RuntimeError, my_filter.analyse)
            arguments["parameter"] = 14
            my_filter = Rsi(arguments, TEST_LOGGER)
            status = my_filter.analyse()
            TEST_LOGGER.info("%s score is: %s and status %s", symbol[0],
                             my_filter.get_calculation(), status)
            npt.assert_almost_equal(my_filter.get_calculation(), symbol[1], decimal=4)
            assert symbol[2] == status


if __name__ == '__main__':
    unittest.main()
