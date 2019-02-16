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
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from autotrader.datasource.database.stock_schema import BARS_NUMPY
from autotrader.indicators.base_indicator import BaseIndicator
from autotrader.tool.indicators.back_testing import BackTesting


class Optimizer:
    """ Optimizer tool for strategies
    The optimizer iterate over all possible arguments to find the combination
    with the best earnings.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def run_optimizer(self, optimizer_values, strategy, stock_bars, last_price=None):
        """

        :param optimizer_values: list of list with arguments
        :param strategy:  strategy object
        :param stock_bars:  bars of stock
        :param last_price: added to price dataframe. Useful when db is not in
        sync with newest values.
        :return: maximal profit, optimized arguments, status (buy, sell ...)
        """
        # optimize parameters
        profit_max = - 2000
        param_max = None
        status = BaseIndicator.NO_SIGNAL
        for optimizer_value in optimizer_values:
            try:
                profit, status = self.calc_profit(
                    strategy,
                    stock_bars,
                    optimizer_value,
                    last_price
                )
                if profit > profit_max:
                    profit_max = profit
                    param_max = optimizer_value
            except ValueError:
                self.logger.debug("Arguments %s causes errors", optimizer_value)
                continue
        return profit_max, param_max, status

    def calc_profit(self, strategy, stock_bars, optimizer_value, last_price=None):
        """
        Calculates the profit
        :param strategy: strategy object
        :param stock_bars: bars of stock
        :param optimizer_value: arguments for strategy
        :param last_price: added to price dataframe. Useful when db is not in
        sync with newest values.
        :return: profit and status
        """
        if not strategy.has_bars() and stock_bars is not None:
            # skip if strategies has bars. Used for unit tests
            strategy.set_bars(
                stock_bars
            )
        strategy.append_value_to_bars(last_price)
        strategy.set_parameters(optimizer_value)
        signal = strategy.generate_signals()
        status = strategy.get_status(signal)
        test = BackTesting(strategy.symbol, strategy, signal)
        profit = test.backtest_portfolio(strategy.plot_result)
        profit = profit[-1] / test.arguments['initial_capital'] - 1
        self.logger.debug("Signal %s(%s) earns %s and has status code %s" %
                          (strategy.name, strategy.parameters, profit, status))
        return profit, status
