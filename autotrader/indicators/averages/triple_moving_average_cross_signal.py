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


class TripleMovingAverageCrossSignal(BaseIndicator):
    """
    TripleMovingAverageCrossSignal

    Intersecting the short average with the medium average indicates a trend change here,
    but the entry into a long position occurs only when both the short average and the medium
    average are above the long average. The exit occurs as soon as the short
    average falls below the medium average.

    The argument['parameters'] must contain the following values:
            'short_window': 4,
            'medium_window': 9,
            'long_window': 18

    """

    NAME = 'TripleMovingAverageCrossSignal'
    SHORT_NAME = 'Tmacs'
    SHORT = 4
    MEDIUM = 9
    LONG = 18

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [SHORT,
                       MEDIUM,
                       LONG],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, argument: dict, logger: logging.Logger):
        super(TripleMovingAverageCrossSignal, self).__init__(argument, logger)
        self.strategy_value = {
            'short_window': 0,
            'medium_window': 0,
            'long_window': 0
        }
        self.param_count = 3
        self.set_parameters(argument['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count:
            raise ValueError("The strategy needs {} arguments".format(self.param_count))
        self.parameters = parameters
        self.strategy_value['short_window'] = parameters[0]
        self.strategy_value['medium_window'] = parameters[1]
        self.strategy_value['long_window'] = parameters[2]

    def get_indicators(self):
        short_mavg = ti.sma(self.open, int(self.strategy_value['short_window']))
        medium_mavg = ti.sma(self.open, int(self.strategy_value['medium_window']))
        long = ti.sma(self.open, int(self.strategy_value['long_window']))
        return short_mavg, medium_mavg, long

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the indicators
        to go long, short or hold (1, -1 or 0)."""
        long_window = int(self.strategy_value['long_window'])
        medium_window = int(self.strategy_value['medium_window'])
        short_window = int(self.strategy_value['short_window'])
        short_mavg, medium_mavg, long = self.get_indicators()

        self.signal = np.zeros(long.shape, dtype='int')
        offset_s = long_window - short_window
        offset_m = long_window - medium_window
        short = short_mavg[offset_s:]
        medium = medium_mavg[offset_m:]
        signal_long_indices = np.where((short > medium) & (short > long) & (medium > long))
        signal_short_indices = np.where(medium > short)
        self.signal[signal_long_indices] = 1
        self.signal[signal_short_indices] = 0
        self.signal = BaseIndicator.set_signal(self.signal)
        self.signal_shift = long_window - 1
        if self.plot_result:
            self.plot([self.times, self.close, self.open, medium, short, long])
        return self.signal

    def plot(self, graphs):
        shift = self.signal_shift
        price_open = graphs[2]
        times = graphs[0]
        short = graphs[3]
        medium = graphs[4]
        long = graphs[4]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, price_open, color='r', lw=2.)
        ax1.plot(times[shift:], short, lw=2.)
        ax1.plot(times[shift:], medium, lw=2.)
        ax1.plot(times[shift:], long, lw=2.)
        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[self.signal_shift:][indices_buy],
                 price_open[self.signal_shift:][indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[self.signal_shift:][indices_sell],
                 price_open[self.signal_shift:][indices_sell],
                 'v', markersize=10, color='r')
        fig.show()
