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


class MovingAverageCrossSignal(BaseIndicator):
    """
    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    parameters - List with Lookback period for short moving average [0]
    and long moving average [1]. Length must be 2.
    logger - logger object
    name = name of strategy is used for db import
    optimizable = set the flag for optimizer
    """

    NAME = 'MovingAverageCrossSignal'
    SHORT_NAME = 'Macs'
    SHORT = 30
    LONG = 90

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [SHORT,
                       LONG],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, argument: dict, logger: logging.Logger):
        super(MovingAverageCrossSignal, self).__init__(argument, logger)
        self.strategy_value = {
            'short_window': 0,
            'long_window': 0,
        }
        self.param_count = 2
        self.set_parameters(argument['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count:
            raise ValueError("The strategy needs {} arguments".format(self.param_count))
        self.parameters = parameters
        self.strategy_value['short_window'] = parameters[0]
        self.strategy_value['long_window'] = parameters[1]

    def get_indicators(self):
        short_mavg = ti.sma(self.open, int(self.strategy_value['short_window']))
        long_mavg = ti.sma(self.open, int(self.strategy_value['long_window']))
        return short_mavg, long_mavg

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the indicators
        to go long, short or hold (1, -1 or 0)."""
        long_window = int(self.strategy_value['long_window'])
        short_window = int(self.strategy_value['short_window'])
        short_mavg, long_mavg = self.get_indicators()
        # Create a 'signal' (invested or not invested) when the short moving average crosses the
        # long moving average, but only for the period greater than the shortest moving average
        # window
        self.signal = np.zeros(long_mavg.shape, dtype='int')
        offset = long_window-short_window
        signal_indices = np.where(short_mavg[offset:] > long_mavg)
        self.signal[signal_indices] = 1
        self.signal = BaseIndicator.set_signal(self.signal)
        self.signal_shift = long_window - 1
        if self.plot_result:
            self.plot([self.times, self.close, self.open, short_mavg, long_mavg])
        return self.signal

    def plot(self, graphs):
        long_window = self.strategy_value['long_window']
        short_window = self.strategy_value['short_window']
        openp = graphs[2]
        times = graphs[0]
        short_mavg = graphs[3]
        long_mavg = graphs[4]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, openp, color='r', lw=2.)
        ax1.plot(times[short_window-1:], short_mavg, lw=2.)
        ax1.plot(times[long_window-1:], long_mavg, lw=2.)
        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[self.signal_shift:][indices_buy],
                 openp[self.signal_shift:][indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[self.signal_shift:][indices_sell],
                 openp[self.signal_shift:][indices_sell],
                 'v', markersize=10, color='r')
        fig.show()
