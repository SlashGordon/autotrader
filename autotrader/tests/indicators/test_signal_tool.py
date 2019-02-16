# -*- coding: utf-8 -*-
""" Autotrader

 Copyright 2017-2017 Slash Gordon

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
import logging
import os
import unittest
import datetime
from freezegun import freeze_time
from autotrader.base.trader_base import TraderBase
from autotrader.datasource.database.stock_schema import Stock, Signal, Orders, OrderType, Status, \
    Filter, Parameter, Plot, BARS_NUMPY
from autotrader.datasource.database.stock_database import StockDataBase as Db
from autotrader.indicators.trend.aroon_basic import AroonSignal
from autotrader.tool.indicators.build_indicators_back_test import BuildIndicatorsBackTest
from autotrader.tool.indicators.build_indicators_full import BuildIndicators


class TestSignalTool(unittest.TestCase):
    """
    Tests the signal generator tool
    """

    @classmethod
    def setUpClass(cls):
        """
        create test basics
        :return:
        """
        cls.config = TraderBase.get_config()
        cls.test_logger = logging.getLogger()
        cls.test_logger.setLevel(logging.WARNING)
        cls.db_tool = Db(cls.config['sql'], cls.test_logger)
        cls.db_tool.connect()
        assert 'PYCHARM' in os.environ or cls.config['sql']['address'] == 'mysqltest'

    @classmethod
    def tearDownClass(cls):
        cls.db_tool.session = None

    def setUp(self):
        self.delete_all()

    def tearDown(self):
        self.delete_all()

    @freeze_time("2017-10-02")
    def test1_signal_full(self):
        """
        Tests the signal creation
        :return:
        """
        len_signals_before = len(self.db_tool.session.query(Signal).all())
        arguments = {
            'signals': AroonSignal.SHORT_NAME,
            'stocks': ["ALL"],
            "look_back": 300,
            "db_tool": self.db_tool
        }
        exit_code = BuildIndicators(self.config, arguments, self.test_logger).build()
        assert exit_code == 0
        len_signals_after = len(self.db_tool.session.query(Signal).all())
        assert len_signals_after > len_signals_before
        len_stocks = len(self.db_tool.session.query(Stock).all())
        assert len_signals_after == len_stocks
        len_plot_after = len(self.db_tool.session.query(Plot).all())
        len_parameter_after = len(self.db_tool.session.query(Parameter).all())
        assert len_parameter_after == len_plot_after == len_stocks

    @freeze_time("2017-10-06")
    def test2_signal_quick(self):
        """
        Tests the update precess
        """
        self.test1_signal_full()
        my_signals = self.db_tool.session.query(Signal).all()
        len_signals_after = len(my_signals)
        len_stocks = len(self.db_tool.session.query(Stock).all())
        assert len_signals_after == len_stocks
        arguments = {
            'signals': AroonSignal.SHORT_NAME,
            'stocks': ["ALL"],
            'look_back': 300,
            'offline': True,
            'db_tool': self.db_tool
        }
        exit_code = BuildIndicatorsBackTest(self.config, arguments, self.test_logger).build()
        assert exit_code == 0
        self.db_tool.session = None
        self.db_tool = Db(self.config['sql'], self.test_logger)
        self.db_tool.connect()
        my_signals = self.db_tool.session.query(Signal).all()
        len_signals_after = len(my_signals)
        assert len_signals_after == len_stocks
        len_plot_after = len(self.db_tool.session.query(Plot).all())
        len_parameter_after = len(self.db_tool.session.query(Parameter).all())
        assert len_parameter_after == len_plot_after == len_signals_after
        for my_signal in my_signals:
            now_date = datetime.datetime.now().date()
            refresh_date = my_signal.refresh_date.date()
            assert now_date == refresh_date

    def delete_all(self):
        """
        Deletes all plot, parameter and signal records
        :return:
        """
        self.db_tool.session.query(Plot).delete()
        self.db_tool.session.query(Parameter).delete()
        self.db_tool.session.query(Signal).delete()
        self.db_tool.commit()


if __name__ == '__main__':
    unittest.main()
