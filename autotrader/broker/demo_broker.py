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
import logging
import datetime
import uuid

from autotrader.broker.degiro.degiro_client import DegiroClient
from autotrader.base.trader_base import TraderBase
from autotrader.broker.broker_base import BrokerBase
from autotrader.datasource.database.stock_schema import Portfolio, Stock, Series, Orders,\
    Status, OrderType


class DemoBroker(BrokerBase):
    """
    Demo broker implementation for test purposes only
    """

    BROKER_NAME = "Demo"
    VARIANCE = 0.02

    def __init__(self, demo_config, arguments, logger: logging.Logger):
        super(DemoBroker, self).__init__(DemoBroker.BROKER_NAME, arguments, logger)
        self.portfolio_name = arguments["portfolio_name"]
        self.portfolio_user = arguments["portfolio_user"]
        self.bulk_data = {
            "portfolio": [],
            "portfolio_update": [],
            "order": []
        }
        self.expire_in_hours = 20
        if "expire_in_hours" in arguments:
            self.expire_in_hours = arguments["expire_in_hours"]
        self.client = None
        if not arguments["database_data"]:
            self.client = DegiroClient(demo_config['degiro'], {"db_tool": None}, self.logger)
            self.client.login()
        self.set_portfolio(self.portfolio_name, self.portfolio_user, arguments["cash"])

    def refresh(self, from_date=None, to_date=None):
        """
        Checks if open orders reaches limit price
        :return:
        """
        if self.db_tool.is_connected():
            self.__handle_open_orders()

    def set_portfolio(self, name, user, cash):
        """
        Creates an portfolio by given name
        :param name: name of portfolio
        :param user: name of portfolio owner
        :param cash: initial cash
        :return: nothing
        """
        if name and not self.exist_portfolio(name, user) \
                and self.db_tool.is_connected():
            portfolio = Portfolio(
                name=name,
                user=user,
                cash=cash,
                initial_cash=cash
            )
            self.bulk_data["portfolio"].append(portfolio)
        self.portfolio_name = name
        self.portfolio_user = user

    def delete_portfolio(self, name, user):
        """
        Delete portfolio by given name if exists
        :param name: portfolio name
        :param user: name of portfolio owner
        :return: nothing
        """
        if self.exist_portfolio(name, user) and self.db_tool.is_connected():
            portfolio = self.get_portfolio_object()
            if portfolio and portfolio.id is not None:
                for order in portfolio.orders:
                    self.db_tool.delete(order)
                self.db_tool.delete(portfolio)
            self.__remove_from_bulk(portfolio, "portfolio_update")
            self.__remove_from_bulk(portfolio, "portfolio")

    def __remove_from_bulk(self, portfolio, key):
        if portfolio is None or key is None:
            return
        for idx, item in enumerate(self.bulk_data[key]):
            if item and item.name == portfolio.name and item.user == portfolio.user:
                self.bulk_data[key].pop(idx)
                break

    def exist_portfolio(self, name, user):
        """
        Checks if the portfolio exists
        :param name: the name of portfolio
        :param user: the portfolio owner
        :return: true if exists otherwise false
        """
        portfolio = self.__get_portfolio_object(name, user)
        return portfolio is not None

    def get_cash(self):
        """
        :return: Checks if portfolio exists
        """
        portfolio_cash = self.get_portfolio_object()
        if portfolio_cash:
            return portfolio_cash.cash
        return None

    def set_initial_cash(self, cash):
        portfolio_cash = self.db_tool.session.query(Portfolio.cash)\
            .filter(self.portfolio_name == Portfolio.name)\
            .filter(self.portfolio_user == Portfolio.user).first()
        if portfolio_cash:
            portfolio_cash.cash = cash
        self.db_tool.session.commit()

    def login(self):
        """
        Peform login
        :return:
        """
        self.db_tool.connect()
        if self.client:
            self.client.login()

    def get_commission(self, price):
        """
        Calculates commission of order
        :param price:
        :return: commission of order
        """
        return 2.0 + price * 0.00008

    def __calculate_price(self, close_price: float, order_data: dict, is_sell=False):
        # manipulate price with percentage swift

        price = close_price
        price_complete = price * order_data['size']
        commission = self.get_commission(price_complete)

        if is_sell:
            price_complete -= commission
        else:
            price_complete += commission
            price_complete *= -1

        return price, price_complete, commission

    def set_cash(self, cash):
        """
        Transfer money to your broker
        :param cash: cash to set
        :return:
        """
        portfolio = self.get_portfolio_object()
        if portfolio is not None:
            portfolio.cash += cash
            portfolio.initial_cash += cash

    def get_portfolio_object(self):
        """
        Get portfolio sqlalchemy object
        :return: portfolio object
        """
        return self.__get_portfolio_object(self.portfolio_name, self.portfolio_user)

    def __get_object_portfolio_bulk(self, name, user, key="portfolio"):
        """
        Get portfolio sqlalchemy object by bulk data container
        :return: portfolio object
        """
        portfolio = None
        for item in self.bulk_data[key]:
            if item and item.name == name and item.user == user:
                portfolio = item
                break
        return portfolio

    def __get_portfolio_object(self, name, user):
        """
        Get portfolio sqlalchemy object by bulk data if exists otherwise by database
        :return: portfolio object
        """
        portfolio = self.__get_object_portfolio_bulk(name, user)
        if portfolio is None:
            portfolio = self.__get_object_portfolio_bulk(name, user, "portfolio_update")
        if portfolio is None:
            portfolio = self.db_tool.session.query(Portfolio) \
                .outerjoin(Orders)\
                .join(Stock)\
                .filter(name == Portfolio.name) \
                .filter(user == Portfolio.user).first()
            self.bulk_data["portfolio_update"].append(portfolio)
        return portfolio

    def delete(self, order_uuid: str):
        """
        Delete order by order uuid
        :param order_uuid:
        :return true if deletion was successful otherwise false
        """
        portfolio = self.get_portfolio_object()
        orders = [order for order in portfolio.orders if order.order_uuid == order_uuid
                  and order.status == Status.confirmed]
        order_check = [order for order in portfolio.orders if order.order_uuid == order_uuid
                       and order.status == Status.completed]
        if not order_check and orders:
            remove_idx = []
            for idx, order in enumerate(orders):
                if order.id is not None:
                    self.db_tool.delete(order)
                else:
                    remove_idx.append(idx)
            if remove_idx:
                portfolio.order = [item for idx, item in portfolio.order if idx not in remove_idx]
            return True
        return False

    def get_orders(self, order_uuid: str):
        """
        Get all orders by order uuid
        :param order_uuid:
        :return orders by given uuid
        """
        portfolio = self.get_portfolio_object()
        orders = [order for order in portfolio.orders if order.order_uuid == order_uuid
                  and order.status == Status.confirmed]
        return orders

    def buy(self, stock_id: int, exchange: str, order_data: dict):
        """
        Buy stock
        :param stock_id: stock id
        :param exchange: exchange symbol
        :param order_data: dict with order data
        :return: uuid of order
        """
        order_data["buysell"] = 0
        return self.__order(stock_id, exchange, order_data)

    def sell(self, stock_id: int, exchange: str, order_data: dict):
        """
        Sell stock
        :param stock_id: stock id
        :param exchange: exchange symbol
        :param order_data: dict with order data
        :return: uuid of order
        """
        order_data["buysell"] = 1

        sum_stocks_available = self.get_stock_size(stock_id)

        if sum_stocks_available < order_data["size"]:
            raise RuntimeError("Insufficient stock size. Available {} want to sell {}.".
                               format(sum_stocks_available, order_data["size"]))

        # check if a sell order already executed
        sum_stocks_in_sell_mode = self.get_stock_size_in_sell(stock_id)
        if sum_stocks_available + sum_stocks_in_sell_mode < order_data["size"]:
            raise RuntimeError("Insufficient stock size. Stock already in sell.")

        return self.__order(stock_id, exchange, order_data)

    def get_portfolio_name(self):
        """

        :return: name of given portfolio
        """
        return self.portfolio_name

    def get_portfolio_user(self):
        """

        :return: name of given user
        """
        return self.portfolio_user

    def __order(self, stock_id: int, exchange: str, order_data: dict):

        portfolio = self.get_portfolio_object()

        if not portfolio:
            raise RuntimeError("Portfolio does not exists.")
        my_order = None
        if order_data['size'] < 1:
            raise RuntimeError("Order data has a size smaler 1.")
        stocks = [stock for stock in self.all_stocks
                  if stock.id == stock_id and stock.exchange.symbol == exchange]
        if not stocks:
            raise RuntimeError("Arguments are wrong")
        else:
            stock = stocks[0]
        if order_data["orderType"].value == OrderType.market.value:
            my_order = self.__do_market(stock, order_data, portfolio)
        elif order_data["orderType"].value == OrderType.limit.value:
            my_order = self.__do_limit(stock, order_data, portfolio)

        if not my_order:
            raise RuntimeError("Oder type {} is not supported."
                               .format(order_data["orderType"].value))

        portfolio.orders.append(
            my_order
        )

        portfolio.cash += my_order.price_complete

        if my_order.is_sell:
            self.connect_related_order(my_order)
        return my_order.order_uuid

    def __do_limit(self, stock, order_data: dict, portfolio):
        if "size" not in order_data or "price" not in order_data or order_data['price'] == -1\
                or "buysell" not in order_data:
            raise RuntimeError("Order data is not correct")

        price, price_complete, commission = self.__calculate_price(order_data['price'], order_data,
                                                                   order_data["buysell"] == 1)

        if order_data["buysell"] == 0 and portfolio.cash + price_complete < 0:
            raise RuntimeError("Insufficient Funds: Price {} is higher than cash {}".format(
                price_complete,
                portfolio.cash))

        time_zone = TraderBase.get_timezone()
        now = datetime.datetime.now(time_zone)

        my_order = Orders(
            status=Status.confirmed,
            order_type=OrderType.limit,
            order_uuid=str(uuid.uuid4()),
            size=order_data["size"]*-1 if order_data["buysell"] == 1 else order_data["size"],
            price=price,
            price_complete=price_complete,
            commission=commission,
            stock_id=stock.id,
            signal_id=order_data.get('signal_id'),
            expire_date=datetime.datetime.now(time_zone) +
                        datetime.timedelta(hours=self.expire_in_hours),
            is_sell=True if order_data["buysell"] == 1 else False,
            date=now
        )
        return my_order

    def __do_market(self, stock, order_data: dict, portfolio):
        if "size" not in order_data or "buysell" not in order_data:
            raise RuntimeError("Order data is not correct")

        # get live data
        prices = self.get_last_price(stock)
        # get last stock price by database
        if not prices:
            raise RuntimeError("Couldnt collect price")

        last_price = prices

        price, price_complete, commission = self.__calculate_price(last_price, order_data,
                                                                   order_data["buysell"] == 1)
        if order_data["buysell"] != 1 and (portfolio.cash + price_complete) < 0:
            raise RuntimeError("Insufficient Funds: Price {} is higher"
                               " than cash {}.".format(price, portfolio.cash))
        time_zone = TraderBase.get_timezone()
        now = datetime.datetime.now(time_zone)
        my_order = Orders(
            status=Status.completed,
            order_type=OrderType.market,
            order_uuid=str(uuid.uuid4()),
            size=order_data["size"]*-1 if order_data["buysell"] == 1 else order_data["size"],
            price=price,
            price_complete=price_complete,
            commission=commission,
            stock_id=stock.id,
            signal_id=order_data.get('signal_id'),
            is_sell=True if order_data["buysell"] == 1 else False,
            date=now
            )
        return my_order

    def get_status(self, order_uuid):
        """
        Returns order status by given uuid. If uuid doesn't exist it returns None.
        :param order_uuid: uuid of order
        :return:
        """
        portfolio = self.get_portfolio_object()
        # only take complete orders
        orders = [order for order in portfolio.orders if order.order_uuid == order_uuid]
        if orders:
            order = orders[-1]
            return order.status
        return None

    def get_last_price(self, stock_object, time_zone=None):
        """
        Get last price of stock symbol
        :param stock_object: symbol of stock like ADS
        :param time_zone tz
        :return: last price or None
        """
        time_zone = TraderBase.get_timezone()
        if self.client:
            return self.client.get_last_price(stock_object)
        # get last stock price by database
        price = self.db_tool.session.query(Series)\
            .join(Stock)\
            .filter(Stock.id == stock_object.id)\
            .filter(Series.date <= datetime.datetime.now(time_zone))\
            .order_by(-Series.date).first()

        if not price:
            return None
        return price.priceclose

    @staticmethod
    def __is_exchange_open(exchange: str):
        """

        :param exchange:
        :return:
        """
        time_zone = TraderBase.get_timezone()
        date_now = datetime.datetime.now(time_zone)
        if exchange == 'XETR':
            if date_now.isoweekday() in range(1, 6) and date_now.hour in range(9, 17):
                return True
        elif exchange == 'XFRA':
            if date_now.isoweekday() in range(1, 6) and date_now.hour in range(8, 20):
                return True
        return False

    def __handle_open_orders(self):
        """
        Get all open orders and check if desired price matches with historical stock prices
        :return:
        """
        portfolio = self.get_portfolio_object()
        # only take complete orders
        orders = [order for order in portfolio.orders if order.status == Status.confirmed]
        time_zone = TraderBase.get_timezone()
        now = datetime.datetime.now(time_zone)
        for order in orders:
            price = self.db_tool.session.query(Series)\
                .filter(order.stock_id == Series.stock_id) \
                .filter(Series.date.between(order.date, now)) \
                .filter(order.price >= Series.pricehigh)\
                .order_by(Series.date.asc()).first()
            if price:
                order.status = Status.completed
                order.date = price.date
                self.connect_related_order(order)
            else:
                diff = now - order.date.replace(tzinfo=time_zone)
                hours = diff.total_seconds() / 60
                if hours >= self.expire_in_hours:
                    self.logger.info("Order is expired because limit {} for {} "
                                     "was not reached during the day".
                                     format(order.price, order.stock_id))
                    order.status = Status.expired
                    portfolio.cash -= order.price_complete

    def commit_work(self):
        for portfolio_new in self.bulk_data["portfolio"]:
            self.db_tool.session.add(portfolio_new)
        self.db_tool.commit()
