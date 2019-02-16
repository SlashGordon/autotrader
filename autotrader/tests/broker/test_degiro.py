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
import logging
import unittest
import uuid
from fnmatch import filter

from freezegun import freeze_time
from int_date import to_date
from sqlalchemy.orm import query

from autotrader.base.trader_base import TraderBase
from autotrader.broker.degiro.degiro_client import DegiroClient
from autotrader.broker.degiro.degiro_config_helper import DegiroConfigHelper
from autotrader.datasource.database.stock_database import StockDataBase
from autotrader.datasource.database.stock_schema import OrderType, Orders, \
    Status, Stock, Signal

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)
tz = TraderBase.get_timezone()


class TestDegiro(unittest.TestCase):
    """
    Degiro test suite
    """
    @classmethod
    def setUpClass(cls):
        cls.config = TraderBase.get_config()

        cls.db = StockDataBase(cls.config['sql'], TEST_LOGGER)
        cls.db.connect()
        arguments = {
            "db_tool": cls.db
        }
        cls.client = DegiroClient(cls.config['degiro'], arguments, TEST_LOGGER)
        cls.client.login()

    @classmethod
    def tearDownClass(cls):
        cls.config = None
        cls.client = None
        cls.db = None
    
    def tearDown(self):
        my_portfolio = self.client.get_portfolio_object()
        self.db.session.query(Orders).filter(Orders.portfolio_id == my_portfolio.id). \
            filter(Orders.orders_id > 0).delete()
        self.db.session.query(Orders).filter(Orders.portfolio_id == my_portfolio.id).delete()
        self.db.session.query(Signal).delete()
        self.db.session.query(Stock).filter(Stock.symbol == "NDX1").delete()
        self.db.commit()

    def setUp(self):
        self.tearDown()

    #@unittest.skipIf(datetime.datetime.now(tz).replace(hour=22) >
    #                 datetime.datetime.now(tz) > datetime.datetime.now(tz).replace(hour=5) and
    #                 datetime.datetime.today().weekday() < 5,
    #                 "Don't test when exchange is open")
    # @unittest.skip("Degiro doesn't like automatic trades.")
    # def test0_degiro(self):
    #     """
    #     Test buy and delete order
    #     :return:
    #     """
    #     assert self.client.read_config()
    #     assert DegiroConfigHelper.get_exchange_id("XETR")
    #     assert DegiroConfigHelper.DEGIRO_CONFIG is not None
    #     assert self.client.get_order_id_of_stock("IFX", "XETR")
    #     stock_ifx = self.db.session.query(Stock).filter(Stock.symbol == 'IFX').first()
    #     self.db.session.add(Signal(
    #         name="TestSignalForDeiro1",
    #         profit_in_percent="1.0",
    #         status=2,
    #         stock_id=stock_ifx.id
    #         )
    #     )
    #     signal_ifx = self.db.session.query(Signal).\
    #         filter(Signal.name == 'TestSignalForDeiro1').first()
    #     assert signal_ifx
    #     order_data = {
    #         "orderType": OrderType.limit,
    #         "price": 0.001,
    #         "size": 1,
    #         "signal_id": signal_ifx.id
    #      }
    #     order_id = self.client.buy("IFX", "XETR", order_data)
    #     # error because price is too small
    #     assert order_id is None
    #     last_price = self.client.get_last_price(stock_ifx)
    #     assert type(last_price) is float and last_price > 0.0
    #     limit_price = last_price * 0.85
    #     order_data["price"] = limit_price
    #     order_id = self.client.buy("IFX", "XETR", order_data)
    #     assert order_id
    #     order_ifx = self.db.session.query(Orders.status).\
    #         filter(Orders.order_uuid == order_id).first()
    #     assert order_ifx
    #     assert order_ifx[0].value == Status.confirmed.value
    #     assert self.client.delete(order_id)
    #     order_ifx = self.db.session.query(Orders.status).\
    #         filter(Orders.order_uuid == order_id).first()
    #     assert order_ifx[0].value == Status.deleted.value
    #     order_data = {
    #         "orderType": OrderType.market,
    #         "size": 1,
    #         "signal_id": signal_ifx.id
    #     }
    #     order_id = self.client.buy("IFX", "XETR", order_data)
    #     assert order_id
    #     order_ifx = self.db.session.query(Orders.status). \
    #         filter(Orders.order_uuid == order_id).first()
    #     assert order_ifx
    #     assert order_ifx.status.value == Status.confirmed.value
    #     self.client.refresh()
    #     order_ifx = self.db.session.query(Orders.status). \
    #         filter(Orders.order_uuid == order_id).first()
    #     assert order_ifx
    #     assert order_ifx.status.value == Status.confirmed.value
    #     assert self.client.delete(order_id)
    #     order_ifx = self.db.session.query(Orders.status).\
    #         filter(Orders.order_uuid == order_id).first()
    #     assert order_ifx[0].value == Status.deleted.value

    @unittest.skip("dont work on weekdays")
    def test0_check_day_data(self):
        assert self.client.login()
        symbols = ["ADS", "MRK"]
        issue_ids = self.client.get_issue_ids_by_stock_symbol(symbols)
        assert len(issue_ids) == 2
        for issue_id in issue_ids:
            data_day = self.client.get_day(issue_id)
            assert data_day is not None
            for series in data_day:
                assert series.date.date() == datetime.datetime.today().date()

    def test1_degiro(self):
        """
        Tests the degiro config helper and essential client methods
        :return: nothing
        """
        assert self.client.read_config()
        assert DegiroConfigHelper.DEGIRO_CONFIG is not None
        test_indices = DegiroConfigHelper.get_country_sym_indices('DE')
        assert test_indices
        dax_symbol = DegiroConfigHelper.get_id_of_index_symbol('DAX')
        assert dax_symbol is not None
        sdax_symbol = DegiroConfigHelper.get_id_of_index_symbol('SDAX')
        assert sdax_symbol is not None
        country_id_de = DegiroConfigHelper.get_country_id('DE')
        assert country_id_de is not None
        indices_id_de = DegiroConfigHelper.get_country_id_indices('DE')
        # sdax and mdax has no product id
        assert len(indices_id_de) == 1
        assert self.client.login()
        symbols = ["ADS", "MRK"]
        issue_ids = self.client.get_issue_ids_by_stock_symbol(symbols)
        assert len(issue_ids) == 2
        for issue_id in issue_ids:
            data = self.client.get_week(issue_id)
            assert data is not None
        issue_ids = self.client.get_issue_ids_by_degiro_id(indices_id_de)
        assert len(issue_ids) == 1

    def test2_degiro_dax(self):
        """
        Tests the amount of dax stocks
        :return: nothing
        """
        dax_stocks = self.client.get_all_stocks_of_index('DAX')
        assert len(dax_stocks) > 10

    def test3_degiro_mdax(self):
        """
        Tests the amount of mdax stocks
        :return: nothing
        """
        mdax_stocks = self.client.get_all_stocks_of_index('MDAX')
        assert len(mdax_stocks) > 10

    def test4_degiro_sdax(self):
        """
        Tests the amount of sdax stocks
        :return: nothing
        """
        sdax_stocks = self.client.get_all_stocks_of_index('SDAX')
        assert len(sdax_stocks) > 10

    def test5_degiro_tecdax(self):
        """
        Tests the amount of tecdax stocks
        :return: nothing
        """
        tecdax_stocks = self.client.get_all_stocks_of_index('TECDAX')
        # assert len(tecdax_stocks) == 29
        assert len(tecdax_stocks) > 10

    def test6_degiro(self):
        """
        get last price by given stock stock
        :return:
        """
        self.db.connect()
        assert self.client.read_config()
        results = self.client.get_last_price(self.db.session.query(Stock).first())
        assert results

    def test7_cash(self):
        """
        tests the cash api of degiro
        :return:
        """
        data = self.client.get_cash()
        assert type(data) is float

    def test8_portfolio(self):
        """
        tests the cash api of degiro
        :return:
        """
        assert True

    def test9_config_urls(self):
        """
        Tests the config urls
        """
        assert "tradingUrl" in self.client.degiro_api_urls

#    def test10_test_status(self):
#        """
#        Tests the degiro status method
#        """
#        data = self.client.get_status("76eed126-da0f-435d-95ed-d1dc0fcefab3")
#        assert data == 'CONFIRMED'
    
    def test11_test_refresh(self):
        """
        Tests refresh method
        """
        my_portfolio = self.client.get_portfolio_object()
        stock_ifx = self.db.session.query(Stock).filter(Stock.symbol == 'IFX').first()
        self.db.session.add(Stock(
            exchange_id=stock_ifx.exchange_id,
            symbol="NDX1",
            name="NORDEX SE",
            category=stock_ifx.category,
            feed_quality=stock_ifx.feed_quality
        ))
        stock_ndx = self.db.session.query(Stock).filter(Stock.symbol == 'NDX1').first()
        assert stock_ifx and stock_ndx
        self.db.session.add(Signal(
            name="TestSignalForDeiro1",
            profit_in_percent="1.0",
            status=2,
            stock_id=stock_ifx.id
        )
        )
        self.db.session.add(Signal(
            name="TestSignalForDeiro2",
            profit_in_percent="1.0",
            status=2,
            stock_id=stock_ndx.id
        )
        )
        signal_ndx = self.db.session.query(Signal).\
            filter(Signal.name == 'TestSignalForDeiro1').first()
        signal_ifx = self.db.session.query(Signal).\
            filter(Signal.name == 'TestSignalForDeiro2').first()

        # let us create a not completed dummy buy order that matches with historical data
        my_portfolio.orders.append(Orders(
            status=Status.confirmed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=64,
            stock_id=stock_ifx.id,
            is_sell=False,
            date=datetime.datetime.strptime('31/07/2017', '%d/%m/%Y'),
            signal_id=signal_ifx.id
            ))
        my_portfolio.orders.append(Orders(
            status=Status.confirmed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=140,
            stock_id=stock_ndx.id,
            is_sell=0,
            date=datetime.datetime.strptime('21/06/2017', '%d/%m/%Y'),
            signal_id=signal_ndx.id
            ))
        my_portfolio.orders.append(Orders(
            status=Status.completed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=120,
            price=10.0,
            price_complete=-1200.0,
            commission=2.09,
            stock_id=stock_ndx.id,
            is_sell=0,
            date=datetime.datetime.strptime('21/06/2017', '%d/%m/%Y')
            ))
        self.client.refresh(from_date=datetime.datetime.strptime('20/06/2017', '%d/%m/%Y'),
                            to_date=datetime.datetime.strptime('01/08/2017', '%d/%m/%Y'))

        ifx_order = self.db.session.query(Orders).\
            filter(Orders.stock_id == stock_ifx.id).first()
        ndx_order = self.db.session.query(Orders).\
            filter(Orders.stock_id == stock_ndx.id).\
            filter(Orders.size == 140).first()

        ndx_order_2 = self.db.session.query(Orders).\
            filter(Orders.stock_id == stock_ndx.id).\
            filter(Orders.size == 120).first()
        assert ifx_order
        assert ifx_order.price_complete == -1181.61
        assert ifx_order.price * ifx_order.size == 1179.52
        assert ifx_order.commission == 2.09
        assert ifx_order.status == Status.completed

        assert ndx_order
        assert ndx_order.price_complete == -1528.12
        assert ndx_order.price * ndx_order.size == 1526.00
        assert ndx_order.commission == 2.12
        assert ndx_order_2
        assert ndx_order_2.status == Status.completed
        assert ndx_order_2.price_complete == -1200.0
        assert ndx_order_2.price * ndx_order_2.size == 1200.0
        assert ndx_order_2.commission == 2.09
        assert ndx_order_2.status == Status.completed
        # let us create a not completed dummy sell order that matches with historical data
        my_portfolio = self.client.get_portfolio_object()
        my_portfolio.orders.append(Orders(
            status=Status.confirmed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=-64,
            stock_id=stock_ifx.id,
            is_sell=1,
            date=datetime.datetime.strptime('01/08/2017', '%d/%m/%Y'),
            signal_id=signal_ifx.id
            ))
        my_portfolio.orders.append(Orders(
            status=Status.confirmed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=-140,
            stock_id=stock_ndx.id,
            is_sell=1,
            date=datetime.datetime.strptime('27/06/2017', '%d/%m/%Y'),
            signal_id=signal_ndx.id
            ))
        self.client.refresh(from_date=datetime.datetime.strptime('20/06/2017', '%d/%m/%Y'),
                            to_date=datetime.datetime.strptime('01/08/2017', '%d/%m/%Y'))

        ifx_order_sell = self.client.db_tool.session.query(Orders).\
            filter(Orders.stock_id == stock_ifx.id).\
            filter(Orders.status == Status.completed).\
            filter(Orders.is_sell == True).first()
        ndx_order_sell = self.client.db_tool.session.query(Orders).\
            filter(Orders.stock_id == stock_ndx.id).\
            filter(Orders.status == Status.completed).\
            filter(Orders.is_sell == True).first()
        assert ifx_order_sell.price_complete == 1197.90
        assert ifx_order_sell.price * ifx_order.size == 1200.0
        assert ifx_order_sell.commission == 2.10
        assert ifx_order_sell.status == Status.completed
        assert ifx_order.orders_id == ifx_order_sell.id

        assert ndx_order_sell.price_complete == 1544.87
        assert ndx_order_sell.price * ndx_order.size == 1547.00
        assert ndx_order_sell.commission == 2.13
        assert ndx_order.orders_id == ndx_order_sell.id
        my_portfolio = self.client.get_portfolio_object()
        my_portfolio.orders.append(Orders(
            status=Status.confirmed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=789,
            stock_id=stock_ifx.id,
            is_sell=0,
            date=datetime.datetime.strptime('01/08/2017', '%d/%m/%Y'),
            signal_id=signal_ifx.id,
            expire_date=datetime.datetime.strptime('01/08/2017 20:00:00', '%d/%m/%Y %H:%M:%S'),
            ))
        with freeze_time("2017-08-01 19:21:34"):
            self.client.refresh()
            check_expire_order = self.client.db_tool.session.query(Orders). \
                filter(Orders.status == Status.confirmed). \
                filter(Orders.size == 789).first()
            assert check_expire_order
        with freeze_time("2017-08-01 20:21:34"):
            self.client.refresh()
            check_expire_order = self.client.db_tool.session.query(Orders). \
                filter(Orders.status == Status.expired). \
                filter(Orders.size == 789).first()
            assert check_expire_order


if __name__ == '__main__':
    unittest.main()
