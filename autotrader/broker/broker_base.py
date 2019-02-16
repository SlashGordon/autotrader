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

from autotrader.datasource.database.stock_schema import Stock, Exchange, Status


class BrokerBase:
    """
    Base class for all autotrader brokers
    """

    def __init__(self, broker_name: str, arguments, logger: logging.Logger):
        self.broker_name = broker_name
        self.logger = logger
        self.portfolio_name = None
        self.portfolio_user = None
        self.db_tool = arguments.get('db_tool', None)
        self.all_stocks = None
        if self.db_tool:
            self.all_stocks = self.db_tool.session.query(Stock).join(Exchange).all()

    def login(self):
        """
        performs login into broker api
        :return: true/false
        """
        raise NotImplementedError

    def buy(self, stock_id: int, exchange: str, order_data: dict):
        """
        performs order buy
        :return: true/false
        """
        raise NotImplementedError

    def sell(self, stock_id: int, exchange: str, order_data: dict):
        """
        performs order sell/short
        :return: true/false
        """
        raise NotImplementedError

    def get_commission(self, price):
        """
        returns the broker commission for a trade
        :return: commission
        """
        raise NotImplementedError

    def set_initial_cash(self, cash):
        """
        Transfare money to broker
        :param cash:
        :return:
        """
        raise NotImplementedError

    def set_portfolio(self, name, user, cash):
        """
        Creates an portfolio by given name
        :param name: name of portfolio
        :param user: name of portfolio owner
        :param cash: initial cash
        :return: nothing
        """
        pass

    def set_portfolio_name(self, name):
        """
        Set the portfolio name of broker instance
        :param name: name of portfolio
        :return:
        """
        self.portfolio_name = name

    def get_portfolio_name(self):
        """
        Returns the name of broker instance
        :return: the portfolio name of broker instance
        """
        return self.portfolio_name

    def get_portfolio_user(self):
        """
        Returns the user name of broker instance
        :return: the user of portfolio of broker instance
        """
        return self.portfolio_user

    def exist_portfolio(self, name, user):
        """
        Checks if the portfolio exists
        :param name: the name of portfolio
        :param user: the portfolio owner
        :return: true if exists otherwise false
        """
        raise NotImplementedError

    def get_cash(self):
        """
        Get actual balance of broker account
        :return:
        """
        raise NotImplementedError

    def get_last_price(self, stock, time_zone=None):
        """
        Get the last price of stock
        :param stock
        :param time_zone tz
        :return:
        """
        raise NotImplementedError

    def get_status(self, order_id):
        """
        Returns the status of order
        :param order_id: order identifier
        :return: status of order
        """
        raise NotImplementedError

    def refresh(self, from_date=None, to_date=None):
        """
                Refresh remote objects like db tool or broker session
        :param from_date:
        :param to_date:
        :return:
        """
        raise NotImplementedError

    def get_portfolio_object(self):
        """
        Get portfolio sqlalchemy object
        :return: portfolio object
        """
        raise NotImplementedError

    def get_stock_size(self, stock_id, status=Status.completed, is_sell=-1):
        """
        Counts available stocks in portfolio
        :param stock_id: stock to count
        :param status: optional status filter
        :param is_sell: optional is sell/buy filter
        :return: amount of stock items
        """
        portfolio = self.get_portfolio_object()
        orders = [order for order in portfolio.orders if order.status == status]
        if is_sell > -1:
            orders = [order for order in orders if order.is_sell == is_sell]
        # count available stocks in portfolio
        sum_stocks_available = 0
        for order in orders:
            if order and order.stock_id and order.stock_id == stock_id:
                sum_stocks_available += order.size
        return sum_stocks_available

    def get_stock_size_in_sell(self, stock):
        """
        Counts stock amount currently in sell mode by limit order
        :param stock: stock to count
        :return: amount of stock items
        """
        return self.get_stock_size(stock, Status.confirmed, 1)

    def get_stock_size_not_complete(self, stock):
        """
        Counts stock amount currently in buy mode by limit order
        :param stock: stock to count
        :return: amount of stock items
        """
        return self.get_stock_size(stock, Status.confirmed, 0)

    def get_portfolio_items(self):
        """
        Get all active items of portfolio
        :return:
        """
        portfolio = self.get_portfolio_object()
        # only take complete orders
        orders = [order for order in portfolio.orders if order.status == Status.completed]
        # get all traded stocks for stock counting
        stocks_orders = list(set([order.stock_id for order in orders]))
        portfolio = []
        for stock_id in stocks_orders:
            stock_size = self.get_stock_size(stock_id)
            if stock_size > 0:
                signal_id = [order.signal_id for order in orders if order.is_sell == 0 and
                             order.stock_id == stock_id][-1]
                portfolio.append({"stock_id": stock_id, "size": stock_size,
                                  "signal_id": signal_id})
        return portfolio

    def connect_related_order(self, sell_order):
        if sell_order.is_sell:
            portfolio = self.get_portfolio_object()
            # only take complete orders
            buy_orders = [order for order in portfolio.orders
                          if order.status == Status.completed and
                          not order.is_sell and
                          sell_order.signal_id == order.signal_id and
                          abs(sell_order.size) == order.size and
                          sell_order.stock_id == order.stock_id]
            # now we have to find buy order with the smallest difference to sell
            related_order = None
            date_diff = None
            for buy_oder in buy_orders:
                date_diff_now = sell_order.date.replace(tzinfo=None) - \
                                buy_oder.date.replace(tzinfo=None)
                if related_order is None:
                    related_order = buy_oder
                    date_diff = date_diff_now
                elif date_diff > date_diff_now:
                    related_order = buy_oder
                    date_diff = date_diff_now
            if related_order is not None:
                sell_order.associated_orders.append(related_order)
                self.logger.info("Order {} is now associated with {}."
                                 .format(related_order, sell_order))
