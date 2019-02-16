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
from autotrader.datasource.database.stock_schema import BARS_NUMPY
from autotrader.tool.indicators.optimizer import Optimizer
from autotrader.datasource.database.stock_database import StockDataBase as Db
from autotrader.datasource.database.stock_schema import Stock
from autotrader.indicators.base_indicator import BaseIndicator


class TestBase(unittest.TestCase):
    """
    Base class for indicator unit tests
    """

    TEST_LOGGER = logging.getLogger()
    TEST_LOGGER.setLevel(logging.WARNING)

    test_strategy = BaseIndicator(None, None)
    test_params = None
    test_stocks = ["LHA", "MRK"]
    test_excepted_results = None

    @staticmethod
    def check_consistency():
        """
        Checks if results are stable. The method must produce same values after n runs.
        """
        config = TraderBase.get_config()
        db_tool = Db(config['sql'], TestBase.TEST_LOGGER)
        db_tool.connect()
        stock = db_tool.session.query(Stock).filter(Stock.symbol == TestBase.test_stocks[1]).first()
        status_list = []
        profits_list = []
        for _ in range(100):
            profit, status = TestBase.calculate_profit(stock, TestBase.test_strategy,
                                                       TestBase.test_params)
            status_list.append(status)
            profits_list.append(profit)
        # check if profit elements are equal and status elements are equal
        assert status_list.count(status_list[0]) == len(status_list)
        assert profits_list.count(profits_list[0]) == len(profits_list)
        db_tool.session.close()

    @staticmethod
    def compare_excepted_with_results():
        """
        Tests two stocks with freezed data set
        """
        config = TraderBase.get_config()
        db_tool = Db(config['sql'], TestBase.TEST_LOGGER)
        db_tool.connect()
        symbols = TestBase.test_stocks
        excepted_results = TestBase.test_excepted_results
        results = []
        # collect results
        for symbol in symbols:
            stock = db_tool.session.query(Stock).filter(symbol == Stock.symbol).first()
            for param in TestBase.test_params:
                results.append(TestBase.calculate_profit(stock, None, param))

        # compare calculated results with excepted results
        for idx, result in enumerate(results):
            TestBase.TEST_LOGGER.info("Profit is %s and status %s", result[0], result[1])
            assert result[1] == excepted_results[idx][1], "Test%s: %s != %s" % (idx, result[1],
                                                                                excepted_results[idx][1])
        db_tool.session.close()

    @staticmethod
    def calculate_profit(stock, strategy, params):
        """
        Calculate profit and status for ema strategy
        :param stock: stock db object
        :param strategy: initialized strategy object
        :param params: params for strategy
        :return:
        """
        arguments = {
            'symbol': stock.symbol,
            'bars': None,
            'parameters': params,
            'optimizable': False,
            'name': TestBase.test_strategy.NAME,
            'plot_result': False
        }

        strategy = TestBase.test_strategy(
            arguments,
            TestBase.TEST_LOGGER
        )

        strategy.set_bars(
            stock.get_bars(
                start=datetime.datetime(2016, 6, 1, 0, 0),
                end=datetime.datetime(2017, 9, 1, 0, 0),
                output_type=BARS_NUMPY
            )
        )

        profit, status = Optimizer(TestBase.TEST_LOGGER).calc_profit(
            strategy,
            None,
            params
        )
        return profit, status
