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
from autotrader.base.trader_base import TraderBase
from autotrader.filter.price_target_score import PriceTargetScore as Pr
from autotrader.datasource.database.stock_database import StockDataBase as Db
from autotrader.datasource.database.stock_schema import Stock, BARS_NUMPY

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestPriceTarget(unittest.TestCase):
    """
    Tests the price target filter
    """

    @staticmethod
    def test_gen_signal():
        """
        Tests two stocks with freezed data set
        """
        config = TraderBase.get_config()
        db_tool = Db(config['sql'], TEST_LOGGER)
        db_tool.connect()
        symbols = [["LHA", 5, 0], ["MRK", -6, 0]]
        for symbol in symbols:
            stock = db_tool.session.query(Stock).filter(symbol[0] == Stock.symbol).first()
            arguments = {
                'stock': stock,
                'name': Pr.NAME,
                'bars': stock.get_bars(output_type=BARS_NUMPY),
                'threshold_buy': 10,
                'threshold_sell': 5,
                'intervals': None,
                'lookback': 2
            }
            my_filter = Pr(arguments, TEST_LOGGER)
            status = my_filter.analyse()
            TEST_LOGGER.info("%s score is: %s and status %s", symbol[0],
                             my_filter.get_calculation(), status)
            assert symbol[1] == my_filter.get_calculation()
            assert symbol[2] == status
            db_tool.session.close()


if __name__ == '__main__':
    unittest.main()
