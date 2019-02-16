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

from freezegun import freeze_time

from autotrader.base.command_line import get_arg_parse, get_from_to_dates, get_stocks
from autotrader.base.trader_base import TraderBase
from autotrader.datasource.database.stock_database import StockDataBase
from autotrader.datasource.database.stock_schema import Signal, Parameter, Plot, Stock
from autotrader.tool.strategy.back_testing import BackTestingStrategy


class TestCommandLine(unittest.TestCase):
    """
    Test for command line
    """

    def test_cmd(self):
        """
        tests the cmd
        :return: nothing
        """
        arg_parse = get_arg_parse(None)
        assert arg_parse is None
        arg_parse = get_arg_parse(['-f'])
        assert arg_parse is not None and arg_parse.filter is not None
        arg_parse = get_arg_parse(['-s'])
        assert arg_parse is not None and arg_parse.signals is not None
        arg_parse = get_arg_parse(['-u', 'ALL'])
        assert arg_parse is not None and arg_parse.update[0] == 'ALL'
        arg_parse = get_arg_parse(['-U', 'ALL'])
        assert arg_parse is not None and arg_parse.updatesheets[0] == 'ALL'
        with self.assertRaises(SystemExit) as exit_exception:
            get_arg_parse(['-c'])
        the_exception = exit_exception.exception
        self.assertEqual(the_exception.code, 2)
        with self.assertRaises(SystemExit) as exit_exception:
            get_arg_parse(['-c', 'some_file_that_not_exist.dat'])
        the_exception = exit_exception.exception
        self.assertEqual(the_exception.code, 2)
        open("file_that_exists.dat", 'a').close()
        arg_parse = get_arg_parse(['-c', 'file_that_exists.dat'])
        assert arg_parse.config == 'file_that_exists.dat'

    def test_date_gen_for_back_test(self):
        """
        Tests the date generator / splitter
        :return:
        """
        from_date, to_date = get_from_to_dates(None, None)
        assert from_date is None and to_date is None
        config = TraderBase.get_config()
        logger = TraderBase.setup_logger("autotrader")
        db_tool = StockDataBase(config["sql"], logger)
        db_tool.connect()
        db_tool.session.query(Plot).delete()
        db_tool.session.query(Parameter).delete()
        db_tool.session.query(Signal).delete()

        stock = db_tool.session.query(Stock).first()
        with freeze_time("2017-10-02 09:54"):
            my_signal = Signal(
                profit_in_percent=1,
                name="TestSignal",
                status=2,
                date=datetime.datetime.now(),
                refresh_date=datetime.datetime.now(),
            )
            stock.signal.append(my_signal)
        with freeze_time("2017-08-02  09:33"):
            my_signal = Signal(
                profit_in_percent=1,
                name="TestSignal",
                status=2,
                date=datetime.datetime.now(),
                refresh_date=datetime.datetime.now(),
            )
            stock.signal.append(my_signal)

        with freeze_time("2017-10-02"):
            my_dates_tasks = [get_from_to_dates(db_tool, [idx, 8]) for idx in range(8)]
            assert len(my_dates_tasks) == 8
            my_dates_tasks_back = []
            for from_date, to_date in my_dates_tasks:
                for my_date in BackTestingStrategy.date_range(from_date, to_date):
                    my_dates_tasks_back.append(my_date)

            my_first_date = db_tool.session.query(Signal.date).order_by(Signal.date).first()
            my_dates_orig = [my_date for my_date in
                             BackTestingStrategy.date_range(my_first_date[0],
                                                            datetime.datetime.now())]
            # assert len(my_dates_orig) == len(my_dates_tasks_back)
            # for idx, my_date_back in enumerate(my_dates_tasks_back):
            #    assert my_date_back == my_dates_orig[idx]
        db_tool.session.rollback()

    def test_get_stocks(self):
        """
        Test stocks splitter
        :return:
        """
        stocks = get_stocks(None, None)
        assert 'ALL' in stocks and len(stocks) == 1
        config = TraderBase.get_config()
        logger = TraderBase.setup_logger("autotrader")
        db_tool = StockDataBase(config["sql"], logger)
        db_tool.connect()
        my_stocks = db_tool.session.query(Stock.id).all()
        my_stocks_orig = [my_stock[0] for my_stock in my_stocks if my_stock]
        my_stocks_tasks = []
        for idx in range(8):
            my_stocks_tasks += get_stocks(db_tool, [idx, 8])

        assert len(my_stocks) == len(my_stocks_tasks)
        for idx, stock_orig in enumerate(my_stocks_orig):
            assert stock_orig == my_stocks_tasks[idx]


if __name__ == '__main__':
    unittest.main()
