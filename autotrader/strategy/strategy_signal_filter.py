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
from datetime import datetime
from autotrader.strategy.strategy_base import StrategyBase


class StrategyFilterSignal(StrategyBase):
    """
    The strategy filters signals depending on the signal characteristics.
    """

    ONLY_BUY_WHEN_ON_RUN = 0

    def __init__(self, config, arguments, broker, my_logger: logging.Logger):
        super(StrategyFilterSignal, self).__init__(config, arguments, broker, my_logger)
        self.threshold = arguments["threshold"]
        self.mode = arguments["mode"]

    def get_relevant_buy_signals(self):
        if self.mode == StrategyFilterSignal.ONLY_BUY_WHEN_ON_RUN:
            return self.only_buy_when_on_run()
        else:
            raise NotImplementedError

    def only_buy_when_on_run(self):
        filtered_signals = []
        buy_signals = super(StrategyFilterSignal, self).get_relevant_buy_signals()

        for buy_signal in buy_signals:
            # extract plot data
            buy_data, sell_data = self.parse_plot_data(buy_signal.plot)
            # count the correct signals in a row
            on_run_ctx = self.on_run_counter(sell_data, buy_data)

            if on_run_ctx == self.threshold:
                filtered_signals.append(buy_signal)

        return filtered_signals

    @staticmethod
    def find_price_helper(search_time, price_list):
        if not (search_time and price_list):
            return None
        for price in price_list['data']:
            search_date = datetime.fromtimestamp(search_time / 1e3).date()
            list_date = datetime.fromtimestamp(price[0] / 1e3).date()
            if search_date == list_date:
                return price[1]
        return None

    @staticmethod
    def parse_plot_data(plot):
        if not (plot and plot[0].data):
            return [], []
        my_json = plot[0].get_plot()
        if my_json is None or not (len(my_json) == 4):
            return [], []

        buy_data = [{
            'time': x['x'],
            'price': StrategyFilterSignal.find_price_helper(x['x'], my_json[0])
        } for x in my_json[1]['data'] if x['text'] == 'Buy']

        sell_data = [{
            'time': x['x'],
            'price': StrategyFilterSignal.find_price_helper(x['x'], my_json[0])
        } for x in my_json[1]['data'] if x['text'] == 'Sell']

        buy_data = sorted(buy_data, key=lambda k: k['time'])
        sell_data = sorted(sell_data, key=lambda k: k['time'])

        if sell_data and buy_data and buy_data[0]['time'] > sell_data[0]['time']:
            sell_data.pop(0)

        if sell_data and buy_data and buy_data[-1]['time'] > sell_data[-1]['time']:
            buy_data = buy_data[:-1]

        return buy_data[::-1], sell_data[::-1]

    @staticmethod
    def on_run_counter(sell_data, buy_data):
        """

        :param sell_data:
        :param buy_data:
        :return:
        """
        if not (sell_data and buy_data):
            return 0
        min_length = min(len(sell_data), len(buy_data))
        on_run_ctx = 0
        if min_length and sell_data and buy_data:
            for idx in range(min_length):
                if sell_data[idx]['price'] > buy_data[idx]['price']:
                    on_run_ctx += 1
                else:
                    return on_run_ctx
        return on_run_ctx
