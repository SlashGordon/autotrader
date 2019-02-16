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


class Stochastic(BaseIndicator):
    """
    The Stochastic Oscillator
    """
    NAME = 'Stochastic'
    SHORT_NAME = 'SO'
    PERIOD = 5
    SLOWING = 3
    D_PERIOD = 3

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': [D_PERIOD, SLOWING, PERIOD],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, arguments: dict, logger: logging.Logger):
        super(Stochastic, self).__init__(arguments, logger)
        self.mode = 1
        self.upper_threshold = 80
        self.lower_threshold = 20
        if 'mode' in arguments:
            self.mode = int(arguments['mode'])
        if 'upper_threshold' in arguments:
            self.upper_threshold = int(arguments['upper_threshold'])
        if 'lower_threshold' in arguments:
            self.lower_threshold = int(arguments['lower_threshold'])
        self.strategy_value = {
            'period': self.PERIOD,
            'slowing_period': self.SLOWING,
            'd_period': self.SLOWING
        }
        self.param_count = 3
        self.set_parameters(arguments['parameters'])

    def set_parameters(self, parameters):
        if not parameters or len(parameters) != self.param_count:
            raise ValueError("The strategy needs {} arguments".format(self.param_count))
        if parameters[0] > parameters[1]:
            raise ValueError("The d_period %s is larger than slowing_period %s",
                             parameters[0], parameters[1])
        self.parameters = parameters
        self.strategy_value = {
            'period': parameters[2],
            'slowing_period': parameters[1],
            'd_period': parameters[0],
        }

    def get_indicators(self):
        period = int(self.strategy_value['period'])
        slowing = int(self.strategy_value['slowing_period'])
        d_period = int(self.strategy_value['d_period'])
        stoch_k, stoch_d = ti.stoch(self.high, self.low, self.close, period, slowing, d_period)
        return stoch_k, stoch_d

    def generate_signals(self):
        stoch_k, stoch_d = self.get_indicators()
        if self.mode == 1:
            # calculate signal for smooth stochastic
            d_signal = np.zeros(stoch_d.shape, dtype='int')
            d_mask_buy = (stoch_d > self.upper_threshold)
            d_signal[d_mask_buy] = 1
            d_mask_sell = (self.lower_threshold > stoch_d)
            d_signal[d_mask_sell] = -1
            self.signal = BaseIndicator.set_signal_osc(d_signal)
        elif self.mode == 2:
            # calculate signal for %k stochastic
            k_signal = np.zeros(stoch_k.shape, dtype='int')
            k_mask_buy = (stoch_k > self.upper_threshold)
            k_signal[k_mask_buy] = 1
            k_mask_sell = (self.lower_threshold > stoch_k)
            k_signal[k_mask_sell] = -1
            self.signal = BaseIndicator.set_signal_osc(k_signal)
        elif self.mode == 3:
            kd_signal = np.zeros(stoch_d.shape, dtype='int')
            kd_mask_buy = (stoch_d > self.upper_threshold) & (stoch_k > self.upper_threshold)
            kd_signal[kd_mask_buy] = 1
            kd_mask_sell = (self.lower_threshold > stoch_d) & (self.lower_threshold > stoch_k)
            kd_signal[kd_mask_sell] = -1
            self.signal = BaseIndicator.set_signal_osc(kd_signal)
        self.signal_shift = abs(len(self.times) - len(stoch_d))
        if self.plot_result:
            self.plot([self.times, self.close, stoch_k, stoch_d])
        return self.signal

    def plot(self, graphs):
        times = graphs[0]
        close = graphs[1]
        stoch_k = graphs[2]
        stoch_d = graphs[3]
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
        ax2 = fig.add_subplot(212, ylabel='so')
        ax2.hlines(y=self.upper_threshold, xmin=times[0], xmax=times[-1], color='g')
        ax2.hlines(y=self.lower_threshold, xmin=times[0], xmax=times[-1], color='r')
        ax2.plot(times[self.signal_shift:], stoch_k, lw=2.)
        ax2.plot(times[self.signal_shift:], stoch_d, lw=2.)

        # ax2.hlines(y=self.lower_threshold, xmin=0.0, xmax=2.0, color='r')
        fig.show()

