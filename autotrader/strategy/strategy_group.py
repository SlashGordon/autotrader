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
from autotrader.strategy.strategy_base import StrategyBase


class StrategyGroup(StrategyBase):
    """
    The strategy has an parameter called group_size with the purpose to buy stocks with signal
    size >= group_siz i.e.
    when Stock ADS has on day x 3 buy signals and group_siz is 2 than the strategy
    starts to buy ADS.

    The strategy uses for the sell signal the indicator with the highest back testing profit.
    """

    def __init__(self, config, arguments, broker, my_logger: logging.Logger):
        self.group_size = 1
        if arguments:
            self.group_size = arguments.get("group_size", self.group_size)
        super(StrategyGroup, self).__init__(config, arguments, broker, my_logger)

    def get_relevant_buy_signals(self):
        buy_signal = super(StrategyGroup, self).get_relevant_buy_signals()
        buy_signal_filter = []
        for sig in buy_signal:
            idxtx = 0
            for sig_cmp in buy_signal:
                if sig.stock.id == sig_cmp.stock.id:
                    idxtx += 1
            if idxtx >= self.group_size:
                buy_signal_filter.append(sig)
        return buy_signal_filter
