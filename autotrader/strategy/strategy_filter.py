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
from datetime import date, datetime, timedelta

from sqlalchemy import func, and_

from autotrader.datasource.database.stock_schema import Signal, Stock, Filter
from autotrader.strategy.strategy_base import StrategyBase


class StrategyFilter(StrategyBase):
    """
    The strategy works in combination with a filter like Levermann or Piotroski i.e.
    only stocks who have the given filter threshold and a buy signal will be buy.
    the threshold is adjustable with the argument entry 'threshold' and with 'filter_name'
    the filter.
    """

    def __init__(self, config, arguments, broker, my_logger: logging.Logger):
        self.threshold_greater = None
        self.threshold_smaller = None
        self.filter_name = arguments["filter_name"]
        if arguments:
            self.ignore_signals = arguments.get("ignore_signals")
            self.threshold_greater = arguments.get("threshold", self.threshold_greater)
            if self.threshold_greater is not None:
                self.threshold_greater = float(self.threshold_greater)
            self.threshold_smaller = arguments.get("threshold_smaller", self.threshold_smaller)
            if self.threshold_smaller is not None:
                self.threshold_smaller = float(self.threshold_smaller)

        super(StrategyFilter, self).__init__(config, arguments, broker, my_logger)

    def get_relevant_buy_signals(self):
        buy_signal = []
        # only take the signal with most profit
        sub_max_profit = self.broker.db_tool.\
            session.query(Signal.stock_id, func.max(Signal.profit_in_percent).label('MaxProfit')) \
            .group_by(Signal.stock_id).all()
        if sub_max_profit is None or len(sub_max_profit) == 0:
            return []
        sub_max_profit = sub_max_profit[0][1] - 0.00009
        if self.threshold_greater:
            buy_signal = self.broker.db_tool.session.query(Signal) \
                .join(Stock) \
                .join(Filter) \
                .filter(Signal.status == 2) \
                .filter(Filter.date.
                        between(datetime.combine((datetime.now() + timedelta(days=-6)).date(),
                                                 datetime.min.time()),
                                datetime.combine(date.today(), datetime.max.time()))) \
                .filter(
                    Signal.refresh_date.between(datetime.combine(date.today(), datetime.min.time()),
                                                datetime.combine(date.today(), datetime.max.time()))
                        ) \
                .filter(Signal.profit_in_percent >= self.threshold_profit) \
                .filter(Signal.profit_in_percent >= sub_max_profit) \
                .filter(Filter.name == self.filter_name) \
                .filter(Filter.value >= self.threshold_greater) \
                .order_by(Signal.profit_in_percent.desc()).all()
        elif self.threshold_smaller:
            buy_signal = self.broker.db_tool.session.query(Signal) \
                .join(Stock) \
                .join(Filter) \
                .filter(Signal.status == 2) \
                .filter(Filter.date.
                        between(datetime.combine((datetime.now() + timedelta(days=-6)).date(),
                                                 datetime.min.time()),
                                datetime.combine(date.today(), datetime.max.time()))) \
                .filter(
                Signal.refresh_date.between(datetime.combine(date.today(), datetime.min.time()),
                                            datetime.combine(date.today(), datetime.max.time()))
                        ) \
                .filter(Signal.profit_in_percent >= self.threshold_profit) \
                .filter(Signal.profit_in_percent >= sub_max_profit) \
                .filter(Filter.name == self.filter_name) \
                .filter(Filter.value <= self.threshold_smaller) \
                .order_by(Signal.profit_in_percent.desc()).all()
        my_filtered_buy_signals = []
        if self.ignore_signals is not None:
            for item in buy_signal:
                if item.name not in self.ignore_signals:
                    my_filtered_buy_signals.append(item)
            # remove duplicates
            return my_filtered_buy_signals
        return buy_signal
