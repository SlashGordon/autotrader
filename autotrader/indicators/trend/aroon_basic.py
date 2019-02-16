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


class AroonSignal(BaseIndicator):
    """
    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    parameters - List with Lookback period and parameter.
    Length of aroon parameter must be 1. The first item is the aroon period.
    logger - logger object
    name = name of strategy is used for db import
    optimizable = set the flag for optimizer
    """

    NAME = 'AroonSignal'
    SHORT_NAME = "Ar"
    PERIOD = 25

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [PERIOD],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, argument: dict, logger: logging.Logger):
        super(AroonSignal, self).__init__(argument, logger)
        self.strategy_value = {
            'period': 0,
        }
        self.param_count = 1
        self.set_parameters(argument['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count:
            raise ValueError("The strategy needs {} arguments".format(self.param_count))
        self.parameters = parameters
        self.strategy_value['period'] = parameters[0]

    def get_indicators(self):
        return ti.aroon(self.high, self.low, int(self.strategy_value['period']))

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the indicators
        to go long, short or hold (1, -1 or 0)."""
        aroon_down, aroon_up = self.get_indicators()

        # Create a 'signal' (invested or not invested) when the short ema crosses the
        # long ema, but only for the period greater than the shortest moving average
        # window
        self.signal = np.zeros(aroon_down.shape, dtype='int')
        signal_indices = np.where(aroon_up > aroon_down)
        self.signal[signal_indices] = 1
        self.signal = BaseIndicator.set_signal(self.signal)
        self.signal_shift = int(self.strategy_value['period'])
        if self.plot_result:
            self.plot([self.times, self.close, self.open, aroon_down, aroon_up])
        return self.signal

    def plot(self, graphs):
        times = graphs[0]
        close_prices = graphs[1]
        # open_prices = graphs[2]
        aroon_down = graphs[3]
        aroon_up = graphs[4]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, close_prices, color='r', lw=2.)
        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[self.signal_shift:][indices_buy],
                 close_prices[self.signal_shift:][indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[self.signal_shift:][indices_sell],
                 close_prices[self.signal_shift:][indices_sell],
                 'v', markersize=10, color='r')
        ax2 = fig.add_subplot(212, ylabel='uo')
        ax2.plot(times[self.signal_shift:], times[self.signal_shift:], aroon_down, aroon_up, lw=2.)
        fig.show()
