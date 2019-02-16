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

import matplotlib.pyplot as plt
import numpy as np
import tulipy as ti

from autotrader.indicators.base_indicator import BaseIndicator


class MacdHistogramSignal(BaseIndicator):
    """
    The buy signals are triggered when the MACD histogram runs below the zero line and turns
    up and the sell-signal is given, when the MACD Histogram tilts down above zero

    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    parameters - List with Lookback period and parameter.
    Length of macd parameter must be 3. The first parameter is the short period,
    second the long period  and at the end the signal period.
    logger - logger object
    name = name of strategy is used for db import
    optimizable = set the flag for optimizer
    """

    NAME = 'MacdSignal'
    SHORT_NAME = 'Macdh'
    SHORT_PERIOD = 12
    LONG_PERIOD = 26
    SIGNAL_PERIOD = 9

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [SHORT_PERIOD, LONG_PERIOD, SIGNAL_PERIOD],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, argument: dict, logger: logging.Logger):
        super(MacdHistogramSignal, self).__init__(argument, logger)
        self.strategy_value = {
            'period': 0,
        }
        self.param_count = 3
        self.set_parameters(argument['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count:
            raise ValueError("The strategy needs {} arguments".format(self.param_count))

        if not parameters[1] > parameters[0]:
            raise ValueError("Given parameters are not in the correct order")
        self.parameters = parameters
        self.strategy_value['short_period'] = parameters[0]
        self.strategy_value['long_period'] = parameters[1]
        self.strategy_value['signal_period'] = parameters[2]

    def get_indicators(self):
        short_period = int(self.strategy_value['short_period'])
        long_period = int(self.strategy_value['long_period'])
        signal_period = int(self.strategy_value['signal_period'])
        return ti.macd(self.open, short_period, long_period, signal_period)

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the indicators
        to go long, short or hold (1, -1 or 0)."""
        long_period = int(self.strategy_value['long_period'])
        macd, macd_signal, macd_histogram = self.get_indicators()
        self.signal = np.zeros(macd_histogram.shape, dtype='int')
        signal_indices_buy = np.where(macd_histogram > 0)
        self.signal[signal_indices_buy] = 1
        self.signal = BaseIndicator.set_signal(self.signal)
        self.signal_shift = long_period - 1
        if self.plot_result:
            self.plot([self.times, self.open, macd_histogram, macd, macd_signal])
        return self.signal

    def plot(self, graphs):
        times = graphs[0]
        open_prices = graphs[1]
        macd_histogram = graphs[2]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, open_prices, color='r', lw=2.)
        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[self.signal_shift:][indices_buy],
                 open_prices[self.signal_shift:][indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[self.signal_shift:][indices_sell],
                 open_prices[self.signal_shift:][indices_sell],
                 'v', markersize=10, color='r')
        ax2 = fig.add_subplot(212, ylabel='uo')
        ax2.plot(times[self.signal_shift:], times[self.signal_shift:], macd_histogram, lw=2.)
        fig.show()
