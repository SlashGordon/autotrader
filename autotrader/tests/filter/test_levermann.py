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
from autotrader.base.trader_base import TraderBase
from autotrader.filter.levermann_score import LevermannScore as Ls
from autotrader.datasource.database.stock_database import StockDataBase as Db
from autotrader.datasource.database.stock_schema import Stock, BARS_NUMPY


TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestLevermann(unittest.TestCase):
    """
    Tests the levermann implementation
    """

    @staticmethod
    def test_levermann():
        """
        Tests two stocks with freezed data set
        """
        config = TraderBase.get_config()
        db_tool = Db(config['sql'], TEST_LOGGER)
        db_tool.connect()
        symbols = [["LHA", 1, 0], ["MRK", -1, 0]]
        for symbol in symbols:
            stock = db_tool.session.query(Stock).filter(symbol[0] == Stock.symbol).first()
            arguments = {
                'stock': stock,
                'name': Ls.NAME,
                'bars': stock.get_bars(
                    start=datetime.datetime(2016, 6, 1, 0, 0),
                    end=datetime.datetime(2017, 9, 1, 0, 0),
                    output_type=BARS_NUMPY),
                'threshold_buy': 7,
                'threshold_sell': 2,
                'intervals': None,
                'lookback': 12
            }
            my_filter = Ls(arguments, TEST_LOGGER)
            status = my_filter.analyse()
            TEST_LOGGER.info("%s score is: %s - %s", symbol[0], my_filter.get_calculation(), status)
            assert symbol[1] == my_filter.get_calculation(),\
                " Calc: %s != %s" % (symbol[1], my_filter.get_calculation())
            assert symbol[2] == status, " Status: %s != %s" % (symbol[2], status)
        db_tool.session.close()


if __name__ == '__main__':
    unittest.main()
