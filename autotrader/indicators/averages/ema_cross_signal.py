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


class EmaCrossSignal(BaseIndicator):
    """
    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    parameters - List with Lookback period, short and long ema parameter.
    Length must be 2.
    logger - logger object
    name = name of strategy is used for db import
    optimizable = set the flag for optimizer
    """

    NAME = 'EmaCrossSignal'
    SHORT_NAME = 'Ema'
    LONG = 150
    SHORT = 40

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [SHORT,
                       LONG],
        'optimizable': False,
        'name': "EmaCrossSignalSignal",
        'plot_result': False
    }

    def __init__(self, argument: dict, logger: logging.Logger):
        super(EmaCrossSignal, self).__init__(argument, logger)
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
        short_ema = ti.ema(self.open, int(self.strategy_value['short_window']))
        long_ema = ti.ema(self.open, int(self.strategy_value['long_window']))
        return short_ema, long_ema

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the indicators
        to go long, short or hold (1, -1 or 0)."""
        short_ema, long_ema = self.get_indicators()
        # Create a 'signal' (invested or not invested) when the short ema crosses the
        # long ema, but only for the period greater than the shortest moving average
        # window
        self.signal = np.zeros(long_ema.shape, dtype='int')
        signal_indices = np.where(short_ema > long_ema)
        self.signal[signal_indices] = 1
        self.signal = BaseIndicator.set_signal(self.signal)
        if self.plot_result:
            self.plot([self.times, self.close, self.open, short_ema, long_ema])
        return self.signal

    def plot(self, graphs):
        openp = graphs[2]
        times = graphs[0]
        short_ema = graphs[3]
        long_ema = graphs[4]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, openp, color='r', lw=2.)
        ax1.plot(times, short_ema, lw=2.)
        ax1.plot(times, long_ema, lw=2.)
        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[indices_buy],
                 openp[indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[indices_sell],
                 openp[indices_sell],
                 'v', markersize=10, color='r')
        fig.show()
