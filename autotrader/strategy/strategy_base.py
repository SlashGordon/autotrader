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
from datetime import date, datetime
import math

from sqlalchemy.sql import and_

from autotrader.datasource.database.stock_schema import OrderType, Status, Signal, Orders, Portfolio
from sqlalchemy import func


class StrategyBase:
    """
    Base class for all strategies
    """

    def __init__(self, config, arguments, broker, my_logger: logging.Logger):
        self.logger = my_logger
        self.broker = broker
        self.order_type = OrderType.market
        self.sell_percentage = 1.0
        self.buy_percentage = 1.0
        self.threshold_profit = .2
        self.threshold_commission_price_ratio = .005
        self.buy_under_value_limit_percentage = .01
        self.sell_over_value_limit_percentage = .005
        self.config = config
        if arguments:
            self.order_type = arguments["order_type"]
            self.sell_percentage = float(
                arguments.get("sell_percentage", self.sell_percentage))
            self.buy_percentage = float(
                arguments.get("buy_percentage", self.buy_percentage))
            self.threshold_profit = float(
                arguments.get("buy_threshold", self.threshold_profit))
            self.threshold_commission_price_ratio = float(
                arguments.get("commission_price_ratio_threshold_",
                              self.threshold_commission_price_ratio))
            self.buy_under_value_limit_percentage = float(
                arguments.get("buy_under_value_limit_percentage",
                              self.buy_under_value_limit_percentage))
            self.sell_over_value_limit_percentage = float(
                arguments.get("sell_over_value_limit_percentage",
                              self.sell_over_value_limit_percentage))
        if not self.broker.exist_portfolio(self.broker.get_portfolio_name(),
                                           self.broker.get_portfolio_user()):
            raise RuntimeError("Portfolio {} doesn't exist."
                               .format(self.broker.get_portfolio_name()))

    def start_strategy(self, buy, sell):
        """
        Executes the strategy
        :param buy: set to false if you want to skip buy
        :param sell: set to false if you want to skip sell
        :return:
        """
        self.broker.refresh()
        if sell:
            portfolio = self.broker.get_portfolio_items()
            sell_signals = self.get_relevant_sell_signals(portfolio)
            if sell_signals:
                self.sell(portfolio, sell_signals)
        if buy:
            buy_signals = self.get_relevant_buy_signals()
            if buy_signals:
                self.buy(buy_signals)

    def sell(self, portfolio, sell_signal):
        """

        :param portfolio:
        :param sell_signal:
        :return:
        """

        for sell in sell_signal:
            cash = self.broker.get_cash()
            amount = self.calculate_sell_amount(portfolio, sell.stock, sell)
            if not self.is_sell_possible(amount):
                continue
            limit_price = -1
            if self.order_type.value == OrderType.limit.value:
                price = self.broker.get_last_price(sell.stock)
                limit_price = price + price * self.sell_over_value_limit_percentage
            order_data = self.get_order_data(self.order_type, amount, sell.id, limit_price)

            try:
                ads_buy_order = self.broker.sell(sell.stock.id, "XETR", order_data)
                status = self.broker.get_status(ads_buy_order)
                if status.value == Status.completed.value:
                    cash_now = self.broker.get_cash()
                    self.logger.info("({}): Sell {} stocks of {} for {}".
                                     format(self.broker.get_portfolio_name(), amount,
                                            sell.stock.symbol, cash_now - cash))
            except RuntimeError:
                self.logger.exception("({}): Trade for {} was not successful.".format(
                    self.broker.get_portfolio_name(),
                    sell.stock.symbol))

    def buy(self, buy_signal):
        """
        :param buy_signal:
        :return:
        """
        for buy in buy_signal:
            cash = self.broker.get_cash()
            price = self.broker.get_last_price(buy.stock)
            amount = self.calculate_buy_amount(price)

            if not self.is_buy_possible(buy.stock, amount, price):
                continue

            limit_price = -1
            if self.order_type.value == OrderType.limit.value:
                limit_price = price - price * self.buy_under_value_limit_percentage
                amount = self.calculate_buy_amount(limit_price)

            order_data = self.get_order_data(self.order_type, amount, buy.id, limit_price)
            try:
                ads_buy_order = self.broker.buy(buy.stock.id, "XETR", order_data)
                if ads_buy_order is None:
                    raise RuntimeError
                status = self.broker.get_status(ads_buy_order)
                if status.value == Status.completed.value:
                    cash_now = self.broker.get_cash()
                    self.logger.info("({}-{}-{}): Buy {} stocks of {} for {}"
                                     .format(self.broker.get_portfolio_name(), buy.name,
                                             buy.profit_in_percent, amount,
                                             buy.stock.symbol,
                                             cash - cash_now))
            except RuntimeError:
                self.logger.exception("({}): Trade for {} was not successful.".format(
                    self.broker.get_portfolio_name(),
                    buy.stock.symbol))

    def get_relevant_sell_signals(self, portfolio):
        """

        :return:
        """
        self.broker.refresh()
        sell_signal_list = []
        if portfolio:
            sell_signal_ids = [item["signal_id"] for item in portfolio]
            sell_signal_list = self.broker.db_tool.session.query(Signal). \
                filter(Signal.id.in_(sell_signal_ids)). \
                filter(Signal.status == -2).all()
        return sell_signal_list

    def get_relevant_buy_signals(self):
        """

        :return:
        """
        # only take the signal with most profit
        # subquery is not working correctly therefore one more query
        sub_max_profit = self.broker.db_tool.session.query(Signal.stock_id,
                                                           func.max(Signal.profit_in_percent)
                                                           .label('MaxProfit')) \
            .group_by(Signal.stock_id).all()
        if sub_max_profit is None or len(sub_max_profit) == 0:
            return []
        # float precession difference between sqlalchemy and python
        sub_max_profit = sub_max_profit[0][1] - 0.00009
        buy_signal = self.broker.db_tool.session.query(Signal) \
            .filter(Signal.status == 2) \
            .filter(Signal.profit_in_percent >= self.threshold_profit) \
            .filter(Signal.profit_in_percent >= sub_max_profit) \
            .filter(Signal.refresh_date.between(datetime.combine(date.today(), datetime.min.time()),
                                                datetime.combine(date.today(), datetime.max.time()))
                    ) \
            .order_by(Signal.profit_in_percent.desc()).all()
        return buy_signal

    def calculate_buy_amount(self, last_price):
        """
        Calculates the amount of stocks to buy. The result depends by your buy percentage value.
        :param last_price: last price of stock
        :return: amount of stocks to buy
        """
        cash = self.broker.get_cash()
        amount = int(cash * self.buy_percentage / last_price)
        return amount

    def calculate_sell_amount(self, portfolio, stock, signal):
        """

        :param portfolio:
        :param stock:
        :param signal:
        :return:
        """
        amount = [int(item['size']) for item in portfolio if item['stock_id'] == stock.id
                  and item['signal_id'] == signal.id]
        if not amount:
            return 0
        amount = int(math.ceil(amount[0] * self.sell_percentage))
        return amount

    def is_sell_possible(self, amount):
        """

        :param amount:
        :return:
        """
        # first check if stock already bought
        if 1 > amount:
            self.logger.warning("Desired amount {} is not tradeable".format(amount))
            return False
        return True

    def is_buy_possible(self, stock, amount, price):
        """
        Returns true if buy is possible by given values otherwise false.
        :param stock: database stock object
        :param amount: amount to buy
        :param price: price of given stock
        :return: true if buy is possible otherwise false
        """
        # first check if stock already bought
        if self.broker.get_stock_size(stock.id) > 0:
            self.logger.warning("Skip buy because {} already in portfolio"
                                .format(stock.symbol))
            return False

        if self.broker.get_stock_size_not_complete(stock.id) > 0:
            self.logger.warning("Skip buy because {} already ordered but not completed"
                                .format(stock.symbol))
            return False

        if amount == 0:
            self.logger.warning("Skip buy because {} because not enough money"
                                .format(stock.symbol))
            return False

        commission = self.broker.get_commission(amount * price)
        commission_price_ratio = commission / (amount * price)
        # skipp if commission compared to buy price is to high
        if commission_price_ratio > self.threshold_commission_price_ratio:
            self.logger.warning("Skip buy because {} commission {} compared to price {} to high"
                                .format(stock.symbol, commission, amount * price))
            return False
        return True

    @staticmethod
    def get_order_data(order_type, amount, signal_id, price=-1):
        """
        Returns order data
        :param order_type: market or limit
        :param amount: amount of stocks to buy
        :param signal_id: signal id
        :param price: set a price in case of limit order
        :return: dictionary with order data
        """
        if order_type.value == OrderType.market.value:
            order_data = {
                "orderType": OrderType.market,
                "timeType": 1,
                "price": -1,
                "size": amount,
                "signal_id": signal_id
            }
        elif order_type.value == OrderType.limit.value:
            order_data = {
                "orderType": OrderType.limit,
                "timeType": 1,
                "price": price,
                "size": amount,
                "signal_id": signal_id
            }
        else:
            raise NotImplementedError
        return order_data
