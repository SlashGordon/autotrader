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
import json
import logging
import sys

from numba import jit
import numpy as np
import zlib
import base64

from autotrader.base.trader_base import TraderBase


class BaseIndicator:
    """
    Base class for indicators
    """

    SELL = -1
    BUY = 1
    HOLD = 0
    NO_SIGNAL = 10

    def __init__(self, argument, logger: logging.Logger):
        self.close = None
        self.open = None
        self.volume = None
        self.high = None
        self.low = None
        self.signal = None
        self.times = None
        self.symbol = None
        self.name = None
        self.parameters = None
        self.plot_result = None
        self.logger = logger
        self.calc = 0
        self.status = 0
        self.signal_shift = 0
        self.param_count = 0
        if argument is not None:
            self.symbol = argument['symbol']
            self.set_bars(argument['bars'])
            self.name = argument['name']
            self.parameters = argument['parameters']
            self.plot_result = argument['plot_result']

    def get_indicators(self):
        """
        Get the indicators of strategy
        :return:
        """
        raise NotImplementedError

    def generate_signals(self):
        """
        Generate the signal
        :return:
        """
        raise NotImplementedError

    def plot(self, graphs: list):
        """
        Plot strategy results
        :param graphs: list with arrays
        :return:
        """
        raise NotImplementedError

    def set_symbol(self, symbol):
        """
        Sett the symbol to strategy
        :param symbol:
        :return:
        """
        self.symbol = symbol

    def set_bars(self, bars):
        """
        Set te bars to strategy
        :param bars:
        :return:
        """
        if bars is not None and hasattr(bars, 'shape') and len(bars.shape) >= 2 and bars.shape[1] == 6:
            self.close = bars[:, 0].copy(order='C').astype('float64')
            self.open = bars[:, 1].copy(order='C').astype('float64')
            self.volume = bars[:, 2].copy(order='C').astype('float64')
            self.high = bars[:, 3].copy(order='C').astype('float64')
            self.low = bars[:, 4].copy(order='C').astype('float64')
            self.times = bars[:, 5].copy(order='C')

    def append_value_to_bars(self, price):
        """
        Append a price to existing bars
        :param price: price to append
        :return: noting
        """
        if price is not None:
            self.close = np.append(self.close, price.priceclose)
            self.open = np.append(self.open, price.priceopen)
            self.volume = np.append(self.volume, price.volume)
            self.high = np.append(self.high, price.pricehigh)
            self.low = np.append(self.low, price.pricelow)
            self.times = np.append(self.times, price.date)

    def get_plot(self):
        """
        Generate plot data for highcharts
        :return: json series string
        """
        tz = TraderBase.get_timezone()
        series_list = [
            {
                "name": "Price",
                "data": [[int(self.times[idx].replace(tzinfo=tz).timestamp()) * 1000, x]
                         for idx, x in enumerate(self.open)],
                "id": 'dataseries'
            },
            {
                "type": 'flags',
                "data": [],
                "onSeries": 'dataseries',
                "shape": 'circlepin',
                "width": 20
            }
        ]
        # we have to generate the siganl again
        signal = self.generate_signals()
        for idx, val in enumerate(signal):
            timestamp = int(self.times[idx + self.signal_shift].replace(tzinfo=tz).timestamp()) * 1000
            if val == 1:
                series_list[1]["data"].append(
                    {
                        "x": timestamp,
                        "title": 'B',
                        "text": 'Buy',
                        "color": "#155724",
                        "fillColor": "#c3e6cb",
                        "style": {
                            "fontFamily": 'monospace',
                            "color": "#155724"
                        }
                    }
                )
            elif val == -1:
                series_list[1]["data"].append(
                    {
                        "x": timestamp,
                        "title": 'S',
                        "text": 'Sell',
                        "color": "#721c24",
                        "fillColor": "#f8d7da",
                        "style": {
                            "fontFamily": 'monospace',
                            "color": "#721c24"
                        }
                    }
                )
        indicators = self.get_indicators()
        for idx, val in enumerate(indicators):
            data_shift = len(series_list[0]["data"]) - val.size
            indicator_values = [None for _ in range(data_shift)]
            for idx2, val2 in enumerate(val):
                timestamp = int(self.times[idx2 + data_shift].replace(tzinfo=tz).timestamp()) * 1000
                indicator_values.append([timestamp, val2])
            series_list.append(
                {
                    "yAxis": 1,
                    "name": "Graph" + str(idx),
                    "data": indicator_values
                }
            )
        my_json_str = json.dumps(series_list)
        my_pack_str = base64.b64encode(zlib.compress(my_json_str.encode("utf-8"), 9))
        size_str = sys.getsizeof(my_json_str)
        size_pack = sys.getsizeof(my_pack_str)
        debug_msg = "Size before {} and size after {}. {}".format(size_str, size_pack,
                                                                  1-size_pack/size_str)
        self.logger.debug(debug_msg)
        return my_pack_str

    def has_bars(self):
        """
        Checks for existing bars
        :return: true if bars existing otherwise false
        """
        if self.close is None:
            return False
        return True

    def set_parameters(self, parameters):
        """
        Set parameters for strategy
        :param parameters:
        :return:
        """
        raise NotImplementedError

    @staticmethod
    @jit(nopython=True)
    def get_status(signal):
        """
        Returns the calculated status of strategy
        :return: buy, sell, hold
        """
        status = 10
        for signal_value in np.nditer(signal):
            if signal[-1] == 1:
                # strong buy
                return 2
            if signal[-1] == -1:
                # strong sell
                return -2

            if signal_value == 1:
                status = 1
            if signal_value == -1:
                status = -1
            if signal_value == 0:
                if status != 1 and status != -1:
                    status = 0
        return status

    @staticmethod
    @jit(nopython=True)
    def set_signal(signal):
        """
        numba optimized function to create standard signal
        :param signal:
        :return: standard signal
        """
        prev_sym = 0
        for idx in range(signal.shape[0]):
            if signal[idx] == 1 and prev_sym == 1:
                prev_sym = 1
                signal[idx] = 0
            elif signal[idx] == 0 and prev_sym == 1:
                prev_sym = -1
                signal[idx] = -1
            elif signal[idx] == 1 and prev_sym == 0:
                prev_sym = 1
                signal[idx] = 1
            elif signal[idx] == 1 and prev_sym == -1:
                prev_sym = 1
                signal[idx] = 1
            else:
                prev_sym = signal[idx]
        return signal

    @staticmethod
    def set_signal_osc(signal):
        """
        numba optimized function to create standard signal for oscillator signals
        :param signal:
        :return: standard signal
        """
        open_pos = False
        for idx in range(signal.shape[0]):
            if signal[idx] == 1 and not open_pos:
                open_pos = True
            elif (signal[idx] == 0 or signal[idx] == 1) and open_pos:
                signal[idx] = 0
            elif signal[idx] == -1 and open_pos:
                open_pos = False
            elif signal[idx] == -1 and not open_pos:
                signal[idx] = 0
        return signal

    @staticmethod
    @jit(nopython=True)
    def fill_signal(signal):
        """
            fill the signals with ones in buy areas
        """
        is_fill = False
        prev_sym = 0
        for idx in range(signal.shape[0]):
            if signal[idx] == 0 and is_fill:
                prev_sym = signal[idx]
                signal[idx] = 1
            elif signal[idx] == 1 and is_fill:
                prev_sym = signal[idx]
                is_fill = False
            elif signal[idx] == 1 and prev_sym == 0:
                prev_sym = signal[idx]
                is_fill = True
            elif signal[idx] == 1 and prev_sym == 1:
                signal[idx] = 0
            else:
                prev_sym = signal[idx]
        return signal
