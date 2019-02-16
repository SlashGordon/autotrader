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
from datetime import timedelta
from freezegun import freeze_time

from autotrader.base.trader_base import TraderBase
from autotrader.broker.demo_broker import DemoBroker
from autotrader.datasource.database.stock_schema import Portfolio, OrderType, Orders, Stock,\
    Series, Status
from autotrader.datasource.database.stock_database import StockDataBase as Db

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestDemo(unittest.TestCase):
    """
    Demo broker test suite
    """

    @classmethod
    def setUpClass(cls):
        cls.config = TraderBase.get_config()
        cls.config = TraderBase.get_config()
        cls.db_tool = Db(cls.config['sql'], TEST_LOGGER)
        cls.db_tool.connect()

    @classmethod
    def tearDownClass(cls):
        cls.db_tool.session.close()
        cls.config = None
        cls.db_tool = None

    def setUp(self):
        self.delete_all()

    def tearDown(self):
        self.delete_all()

    def test1_portfolio(self):
        """
        Test portfolio creation/setup
        :return:
        """
        portfolio_name = "degiro"
        portfolio_user = "user"
        arguments = {
            "portfolio_name": portfolio_name,
            "portfolio_user": portfolio_user,
            "database_data": True,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        portfolios = list(
            self.db_tool.session.query(Portfolio).filter(portfolio_name == Portfolio.name)
        )
        assert len(portfolios) == 0
        broker = DemoBroker(self.config, arguments, TEST_LOGGER)
        broker.set_portfolio(portfolio_name, portfolio_user, 2000)
        assert broker.exist_portfolio(portfolio_name, portfolio_user)
        broker.commit_work()
        portfolios = list(
            broker.db_tool.session.query(Portfolio).filter(portfolio_name == Portfolio.name)
            .filter(portfolio_user == Portfolio.user)
        )
        assert len(portfolios) == 1
        assert portfolios[0].name == portfolio_name
        broker.delete_portfolio(portfolio_name, portfolio_user)
        portfolios = list(
            broker.db_tool.session.query(Portfolio).filter(portfolio_name == Portfolio.name)
        )
        assert not portfolios

    @freeze_time("2017-10-09")
    def test1_price(self):
        """
        Tests if live data and offline data works
        :return:
        """
        arguments = {
            "portfolio_name": "",
            "portfolio_user": "user",
            "database_data": True,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        broker_offline_price = DemoBroker(self.config, arguments, TEST_LOGGER)
        arguments_live = {
            "portfolio_name": "",
            "portfolio_user": "user",
            "database_data": False,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        broker_live_price = DemoBroker(self.config, arguments_live, TEST_LOGGER)
        stock_ads = broker_live_price.db_tool.session.query(Stock).\
            filter(Stock.symbol == 'ADS').first()
        live_price = broker_live_price.get_last_price(stock_ads)
        offline_price = broker_offline_price.get_last_price(stock_ads)
        unittest.skipIf(live_price is None, "Test host is offline.")
        assert live_price != offline_price

    def test2_trade(self):
        """
        Test order sell/buy
        :return:
        """
        portfolio_name = "degiro"
        portfolio_user = "user"
        arguments = {
            "portfolio_name": portfolio_name,
            "portfolio_user": portfolio_user,
            "database_data": True,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        broker = DemoBroker(self.config, arguments, TEST_LOGGER)
        broker.delete_portfolio(portfolio_name, portfolio_user)
        self.db_tool.commit()
        broker.set_portfolio(portfolio_name, portfolio_user, 2000)
        order_data = {
            "orderType": OrderType.market,
            "timeType": 1,
            "price": -1,
            "size": 5
        }
        ads = self.db_tool.session.query(Stock).filter(Stock.symbol == 'ADS').first()
        ifx = self.db_tool.session.query(Stock).filter(Stock.symbol == 'IFX').first()
        lha = self.db_tool.session.query(Stock).filter(Stock.symbol == 'LHA').first()
        assert ads and ifx and lha
        self.assertRaises(RuntimeError, broker.buy, -1, "XETR", order_data)
        self.assertRaises(RuntimeError, broker.buy, ads.id, "TR", order_data)
        order_id = broker.buy(ads.id, "XETR", order_data)
        broker.commit_work()
        orders_by_id = list(broker.db_tool.session.query(Orders)
                            .filter(Orders.order_uuid == order_id))
        assert len(orders_by_id) == 1
        order_data["size"] = 5000
        self.assertRaises(RuntimeError, broker.buy, ads.id, "XETR", order_data)
        order_data["size"] = 6
        self.assertRaises(RuntimeError, broker.sell, ads.id, "XETR", order_data)
        order_data["size"] = 5
        order_id = broker.sell(ads.id, "XETR", order_data)
        orders_by_id = list(
            broker.db_tool.session.query(Orders).filter(Orders.order_uuid == order_id))
        assert len(orders_by_id) == 1
        broker.delete_portfolio(portfolio_name, portfolio_user)
        broker.commit_work()
        broker.set_portfolio(portfolio_name, portfolio_user, 4000)
        broker.buy(ads.id, "XETR", order_data)
        broker.buy(ifx.id, "XETR", order_data)
        broker.buy(lha.id, "XETR", order_data)
        broker.sell(ads.id, "XETR", order_data)
        broker.sell(ifx.id, "XETR", order_data)
        order_data["size"] = 1
        broker.sell(lha.id, "XETR", order_data)
        broker.sell(lha.id, "XETR", order_data)
        broker.sell(lha.id, "XETR", order_data)
        broker.sell(lha.id, "XETR", order_data)
        broker.sell(lha.id, "XETR", order_data)
        self.assertRaises(RuntimeError, broker.sell, lha.id, "XETR", order_data)
        order_data = {
            "orderType": OrderType.limit,
            "timeType": 1,
            "price": 15.25,
            "size": 5
        }
        order_id_limit = broker.buy(ifx.id, "XETR", order_data)
        assert order_id_limit
        orders_by_id = list(
            broker.db_tool.session.query(Orders).filter(Orders.order_uuid == order_id_limit))
        assert not orders_by_id
        broker.commit_work()
        orders_by_id = list(
            broker.db_tool.session.query(Orders).filter(Orders.order_uuid == order_id_limit))
        assert len(orders_by_id) == 1
        portfolio = broker.get_portfolio_object()
        assert portfolio
        broker.delete_portfolio(portfolio_name, portfolio_user)
        portfolio = broker.get_portfolio_object()
        assert portfolio is None
        db_tool_new = Db(self.config['sql'], TEST_LOGGER)
        db_tool_new.connect()
        broker.db_tool = db_tool_new
        portfolio = broker.get_portfolio_object()
        assert portfolio
        db_tool_new.session.close()

    def test3_trade_limit(self):
        """
        Test limit orders
        :return:
        """
        portfolio_name = "degiro"
        portfolio_user = "user"
        arguments = {
            "portfolio_name": portfolio_name,
            "portfolio_user": portfolio_user,
            "database_data": False,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        broker = DemoBroker(self.config, arguments, TEST_LOGGER)
        broker.delete_portfolio(portfolio_name, portfolio_user)
        broker.set_portfolio(portfolio_name, portfolio_user, 50000)
        ads = broker.db_tool.session.query(Stock).\
            join(Series).filter(Stock.symbol == 'ADS').first()
        prices = broker.db_tool.session.query(Series)\
            .filter(Series.stock_id == ads.id)\
            .filter(Series.resolution == 'P1D').order_by(Series.date.asc()).first()
        assert prices
        order_data = {
            "orderType": OrderType.limit,
            "timeType": 1,
            "price": prices.pricehigh + 6,
            "size": 5
        }
        fake_date = prices.date + timedelta(days=2)
        with freeze_time(fake_date):
            order_id_limit = broker.buy(ads.id, "XETR", order_data)
            order_status = broker.get_status(order_id_limit)
            assert order_status.value == Status.confirmed.value

        fake_time_buy = fake_date + timedelta(days=10)
        with freeze_time(fake_time_buy):
            broker.refresh()
            order_status = broker.get_status(order_id_limit)
            assert order_status.value == Status.completed.value
            assert 5 == broker.get_stock_size(ads.id)

        # check if delete of orders works when duration limit is reached
        cash_before = broker.get_cash()
        stock_ads_size_before = broker.get_stock_size(ads.id)
        order_data = {
            "orderType": OrderType.limit,
            "timeType": 1,
            "price": prices.pricehigh-prices.pricehigh*0.9,
            "size": 5
        }
        fake_date = prices.date + timedelta(days=2)
        with freeze_time(fake_date):
            order_id_limit = broker.buy(ads.id, "XETR", order_data)
            order_status = broker.get_status(order_id_limit)
            assert order_status.value == Status.confirmed.value
        stock_ads_size_after = broker.get_stock_size(ads.id)
        assert stock_ads_size_before == stock_ads_size_after
        fake_time_buy = fake_date + timedelta(days=3)
        with freeze_time(fake_time_buy):
            broker.refresh()
            order_status = broker.get_status(order_id_limit)
            assert order_status.value == Status.expired.value
            cash_after = broker.get_cash()
            stock_ads_size_after = broker.get_stock_size(ads.id)
            assert cash_after == cash_before
            assert stock_ads_size_before == stock_ads_size_after
        # check if multiple sell of the same amount fails
        order_data = {
            "orderType": OrderType.limit,
            "timeType": 1,
            "price": prices.pricehigh-prices.pricehigh*0.9,
            "size": float(stock_ads_size_after)
        }

        order_id_limit = broker.sell(ads.id, "XETR", order_data)
        order_status = broker.get_status(order_id_limit)
        assert order_status.value == Status.confirmed.value
        self.assertRaises(RuntimeError, broker.sell, ads.id, "XETR", order_data)
        # check if amount of 0 fails
        order_data = {
            "orderType": OrderType.market,
            "timeType": 1,
            "price": prices.pricehigh-prices.pricehigh*0.9,
            "size": 0
        }
        self.assertRaises(RuntimeError, broker.sell, ads.id, "XETR", order_data)
        self.assertRaises(RuntimeError, broker.buy, ads.id, "XETR", order_data)

    def test4_portfolio(self):
        """
        Test sell
        :return:
        """
        portfolio_name = "degiro"
        portfolio_user = "user"
        arguments = {
            "portfolio_name": portfolio_name,
            "portfolio_user": "user",
            "database_data": False,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        broker = DemoBroker(self.config, arguments, TEST_LOGGER)
        broker.delete_portfolio(portfolio_name, portfolio_user)
        broker.set_portfolio(portfolio_name, portfolio_user, 50000)
        order_data = {
            "orderType": OrderType.market,
            "timeType": 1,
            "price": -1,
            "size": 5
        }
        ads = self.db_tool.session.query(Stock).filter(Stock.symbol == 'ADS').first()
        ifx = self.db_tool.session.query(Stock).filter(Stock.symbol == 'IFX').first()
        lha = self.db_tool.session.query(Stock).filter(Stock.symbol == 'LHA').first()
        assert ads and ifx and lha
        ads_buy_order = broker.buy(ads.id, "XETR", order_data)
        assert ads_buy_order
        order_data["size"] = 10
        ifx_buy_order = broker.buy(ifx.id, "XETR", order_data)
        assert ifx_buy_order
        order_data["size"] = 12
        lha_buy_order = broker.buy(lha.id, "XETR", order_data)
        assert lha_buy_order
        assert broker.get_stock_size(ads.id) == 5
        assert broker.get_stock_size(ifx.id) == 10
        assert broker.get_stock_size(lha.id) == 12
        portfolio = broker.get_portfolio_object()
        assert portfolio.initial_cash > portfolio.cash
        order_data["size"] = 7
        lha_sell_order = broker.sell(lha.id, "XETR", order_data)
        assert lha_sell_order
        assert broker.get_stock_size(lha.id) == 5
        portfolio_items = broker.get_portfolio_items()
        assert portfolio_items
        for item in portfolio_items:
            if item["stock_id"] == ads.id:
                assert item["size"] == 5
            elif item["stock_id"] == ifx.id:
                assert item["size"] == 10
            elif item["stock_id"] == lha.id:
                assert item["size"] == 5

        broker.set_cash(500)

        assert portfolio.initial_cash == (50000 + 500)
        assert portfolio.initial_cash > portfolio.cash

    def delete_all(self):
        self.db_tool.session.query(Orders).filter(Orders.orders_id >= 0).delete()
        self.db_tool.session.query(Orders).delete()
        self.db_tool.session.query(Portfolio).delete()
        self.db_tool.commit()


if __name__ == '__main__':
    unittest.main()
