# -*- coding: utf-8 -*-
""" Autotrader

 Copyright 2017-2017 Slash Gordon

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


class Kvo(BaseIndicator):
    """
    The Klinger Oscillator
    """
    NAME = 'KlingerOscillator'
    SHORT_NAME = 'Kvo'
    SHORT = 34
    LONG = 55
    SIGNAL = 13

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [SHORT, LONG, SIGNAL],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, arguments: dict, logger: logging.Logger):
        super(Kvo, self).__init__(arguments, logger)
        self.strategy_value = {
            'short_window': self.SHORT,
            'long_window': self.LONG,
            'signal_window': self.SIGNAL
        }
        self.param_count = 3
        self.set_parameters(arguments['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count or (parameters[1] < parameters[0]):
            raise ValueError("The strategy needs {} arguments".format(self.param_count))
        self.parameters = parameters
        self.strategy_value = {
            'short_window': parameters[0],
            'long_window': parameters[1],
            'signal_window': parameters[2],
        }

    def get_indicators(self):
        short_window = int(self.strategy_value['short_window'])
        long_window = int(self.strategy_value['long_window'])
        signal_window = int(self.strategy_value['signal_window'])
        kvo = ti.kvo(self.high, self.low, self.close, self.volume, short_window, long_window)
        return kvo, ti.ema(kvo, signal_window)

    def generate_signals(self):
        kvo, kvo_signal = self.get_indicators()
        self.signal = np.zeros(kvo.shape, dtype='int')
        mask_buy = (kvo_signal > kvo)
        self.signal[mask_buy] = 1
        mask_sell = (kvo > kvo_signal)
        self.signal[mask_sell] = -1
        self.signal = BaseIndicator.set_signal_osc(self.signal)
        self.signal_shift = 1
        if self.plot_result:
            self.plot([self.times, self.close, kvo, kvo_signal])
        return self.signal

    def plot(self, graphs):
        times = graphs[0]
        close = graphs[1]
        kvo = graphs[2]
        signal_kvo = graphs[3]
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        ax1 = fig.add_subplot(211, ylabel='Price in €')
        # Plot the open price overlaid with the moving averages
        ax1.plot(times, close, color='r', lw=2.)

        indices_buy = np.where(self.signal == 1)[0]
        ax1.plot(times[self.signal_shift:][indices_buy],
                 close[self.signal_shift:][indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.signal == -1)[0]
        ax1.plot(times[self.signal_shift:][indices_sell],
                 close[self.signal_shift:][indices_sell],
                 'v', markersize=10, color='r')
        ax2 = fig.add_subplot(212, ylabel='kvo')
        ax2.plot(times[self.signal_shift:], kvo, lw=2.)
        ax2.plot(times[self.signal_shift:], signal_kvo, lw=2.)
        fig.show()
