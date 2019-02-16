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
from autotrader.broker.degiro.degiro_client import DegiroClient
from autotrader.datasource.database.stock_database import StockDataBase
from autotrader.datasource.database.stock_schema import BARS_NUMPY, BARS_PANDAS, Stock
from autotrader.tool.database.create_and_fill_database import CreateAndFillDataBase
from autotrader.tool.database.update_database_stocks import UpdateDataBaseStocks

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)

CONFIG = TraderBase.get_config()
CONFIG['sql']['database'] = 'testdatabase'
DB = StockDataBase(CONFIG['sql'], TEST_LOGGER)


class TestDataBase(unittest.TestCase):
    """
    Test suite for database installer
    """

    @staticmethod
    def test_1_install_db():
        """
        test install db
        :return:
        """
        arguments = {}
        db_tool = StockDataBase(CONFIG["sql"], TEST_LOGGER)
        arguments["db_tool"] = db_tool
        arguments["datasource"] = DegiroClient(CONFIG['degiro'],  {}, TEST_LOGGER)
        db_builder = CreateAndFillDataBase(CONFIG, arguments, TEST_LOGGER)
        db_builder.build()
        DB.connect()
        adidas = DB.session.query(Stock).filter(Stock.name == "Adidas AG").first()
        # check if stock has data
        assert adidas.series
        bars = adidas.get_bars(resolution="PT1S")
        assert not bars
        bars = adidas.get_bars()
        assert bars
        bars = adidas.get_bars(output_type=BARS_NUMPY)
        assert bars.shape[1] > 0
        bars = adidas.get_bars(output_type=BARS_PANDAS)
        assert bars.size > 0
        DB.session.close()

    @staticmethod
    def test_2_test_update_stock():
        """
        test update db
        :return:
        """
        db_tool = StockDataBase(CONFIG["sql"], TEST_LOGGER)
        db_tool.connect()
        arguments = {
            'stocks_to_update': ['ALL'],
            'update_stocks': True,
            'update_sheets': False,
            'db_tool': db_tool,
            'datasource':  DegiroClient(CONFIG['degiro'],  {"db_tool": db_tool}, TEST_LOGGER)
        }
        db_update = UpdateDataBaseStocks(CONFIG, arguments, TEST_LOGGER)
        db_update.build()

    @staticmethod
    def test_3_test_update_sheet():
        """
        test update balance and income
        :return:
        """
        db_tool = StockDataBase(CONFIG["sql"], TEST_LOGGER)
        db_tool.connect()
        arguments = {
            'stocks_to_update': ['ALL'],
            'update_stocks': False,
            'update_sheets': True,
            'db_tool': db_tool,
            'datasource':  DegiroClient(CONFIG['degiro'],  {"db_tool": db_tool}, TEST_LOGGER)
        }
        db_update = UpdateDataBaseStocks(CONFIG, arguments, TEST_LOGGER)
        db_update.build()

    @staticmethod
    def test_4_test_query():
        """
        Test final db with queries
        :return:
        """
        DB.connect()
        stocks = DB.session.query(Stock).all()
        assert stocks
        stocks = DB.session.query(Stock).limit(5).all()
        assert len(stocks) == 5
        adidas = DB.session.query(Stock).filter(Stock.name == "Adidas AG").first()
        assert adidas is not None and adidas.name == "Adidas AG"
        bars = adidas.get_bars()
        assert bars
        adidas = DB.session.query(Stock).filter(Stock.name == "Adidas AG").first()
        assert len(adidas.jsondata) == 6
        DB.session.close()


if __name__ == '__main__':
    unittest.main()
