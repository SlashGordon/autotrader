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
from autotrader.strategy.strategy_filter import StrategyFilter


class StrategyOneSignal(StrategyFilter):
    """
    The strategy only follow a specific configured signal
    """

    def __init__(self, config, arguments, broker, my_logger: logging.Logger):
        self.signal_name = arguments["signal_name"]
        super(StrategyOneSignal, self).__init__(config, arguments, broker, my_logger)

    def get_relevant_buy_signals(self):
        buy_signal = []

        for my_signal in super(StrategyOneSignal, self).get_relevant_buy_signals():
            if my_signal.name == self.signal_name:
                buy_signal.append(my_signal)
        return buy_signal
