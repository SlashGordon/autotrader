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


class UltimateOscillatorCrossEma(BaseIndicator):
    """
    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    parameters - List with Lookback period for short, medium and long for UC and period for ema.
    Length must be 4.
    logger - logger object
    name = name of strategy is used for db import
    optimizable = set the flag for optimizer
    """
    NAME = 'UltimateOscillatorCrossEmaSignal'
    SHORT_NAME = 'Uoe'
    SHORT = 7
    MEDIUM = 14
    LONG = 28
    EMA_LONG = 150
    EMA_SHORT = 40

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [EMA_SHORT,
                       EMA_LONG],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, arguments: dict, logger: logging.Logger):
        super(UltimateOscillatorCrossEma, self).__init__(arguments, logger)
        self.strategy_value = {
            'short_window': self.SHORT,
            'medium_window': self.MEDIUM,
            'long_window': self.LONG,
            'ema_window_long': 0,
            'ema_window_short': 0,
            'ema_long': None,
            'ema_short':  None,
            'uc': None
        }
        self.param_count = 2
        self.set_parameters(arguments['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count or (parameters[1] < parameters[0]):
            raise ValueError("The strategy needs {} arguments".format(self.param_count))
        self.parameters = parameters
        self.strategy_value['ema_window_short'] = parameters[0]
        self.strategy_value['ema_window_long'] = parameters[1]

    def get_indicators(self):
        short_window = int(self.strategy_value['short_window'])
        medium_window = int(self.strategy_value['medium_window'])
        long_window = int(self.strategy_value['long_window'])
        ema_window_short = int(self.strategy_value['ema_window_short'])
        ema_window_long = int(self.strategy_value['ema_window_long'])
        ultimate = ti.ultosc(
            self.high,
            self.low,
            self.close,
            short_window,
            medium_window,
            long_window
        )
        ema_long = ti.ema(self.close, ema_window_long)
        ema_short = ti.ema(self.close, ema_window_short)
        return ultimate, ema_short, ema_long

    def generate_signals(self):
        long_window = int(self.strategy_value['long_window'])
        ultimate, ema_short, ema_long = self.get_indicators()
        self.signal = np.zeros(ultimate.shape, dtype='int')
        # find gabs between two overbought areas in uc signal
        uc_signal = np.zeros(ultimate.shape, dtype='int')
        uc_mask = (ultimate > 25) & (ultimate < 75)
        uc_signal[uc_mask] = 1
        # set signals if ema > close and uc in gab
        self.signal_shift = long_window

        signal_indices = np.where(ema_short[self.signal_shift:] > ema_long[self.signal_shift:])
        self.signal[signal_indices] = 1
        mask = (self.signal == 1) & (uc_signal == 1)
        self.signal[self.signal == 1] = 0
        self.signal[mask] = 1
        self.signal[signal_indices] = 1
        self.signal = BaseIndicator.set_signal(self.signal)
        if self.plot_result:
            self.plot([self.times, self.close, ema_long, ema_short, ultimate])
        return self.signal

    def plot(self, graphs):
        times = graphs[0]
        close = graphs[1]
        ema_long = graphs[2]
        ema_short = graphs[3]
        ultimate = graphs[4]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, close, color='r', lw=2.)
        ax1.plot(times, ema_long, lw=2.)
        ax1.plot(times, ema_short, lw=2.)
        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[self.signal_shift:][indices_buy],
                 ema_long[self.signal_shift:][indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[self.signal_shift:][indices_sell],
                 ema_long[self.signal_shift:][indices_sell],
                 'v', markersize=10, color='r')
        ax2 = fig.add_subplot(212, ylabel='uo')
        ax2.plot(times[self.signal_shift:], ultimate, lw=2.)
        fig.show()
