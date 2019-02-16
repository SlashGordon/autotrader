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
import numpy as np
import matplotlib.pyplot as plt
from numba import jit


class BackTesting:
    """
    Encapsulates the notion of a portfolio of positions based
    on a set of indicators as provided by a Strategy.

    Requires:
    symbol - A stock symbol which forms the basis of the portfolio.
    bars - A DataFrame of bars for a symbol set.
    indicators - A pandas DataFrame of indicators (1, 0, -1) for each symbol.
    initial_capital - The amount in cash at the start of the portfolio.
    """

    def __init__(self, symbol, strategy, signal, arguments=None):
        if arguments is None:
            arguments = {
                'initial_capital': 100000.0,
                'commission_rate': 2.,
                'commission_rate_prc': 0.004
            }
        self.arguments = arguments
        self.symbol = symbol
        self.strategy = strategy
        self.signal = signal

    def backtest_portfolio(self, plot_result=False):
        """
        Calculate the possible earnings of given strategy
        :param plot_result: plot portfolio if true
        :return:
        """
        initial_capital = float(self.arguments['initial_capital'])
        commission_rate = float(self.arguments['commission_rate'])
        commission_rate_prc = float(self.arguments['commission_rate_prc'])
        wallet = np.full(self.strategy.signal.shape, initial_capital)
        portfolio = np.full(self.strategy.signal.shape, 0.0)

        total = self.__backtest_portfolio(wallet,
                                          portfolio,
                                          self.strategy.open,
                                          self.signal,
                                          self.strategy.signal_shift,
                                          commission_rate,
                                          commission_rate_prc
                                          )
        if plot_result:
            self.plot(total)
        return total

    @staticmethod
    @jit(nopython=True)
    def __backtest_portfolio(wallet, portfolio, price, signal, signal_offset, commission_rate,
                             commission_rate_prc):
        position = 0
        for index in range(signal.shape[0]):
            if signal[index] == 1:
                position = int(wallet[index]/price[index+signal_offset])
                wallet[index:] -= price[index+signal_offset] * position * \
                    (1 + commission_rate_prc) - commission_rate
                portfolio[index:] += price[index+signal_offset] * position
            if signal[index] == -1:
                wallet[index:] += price[index+signal_offset] * position * \
                                  (1 - commission_rate_prc) - commission_rate
                portfolio[index:] = 0
                position = 0
        total = portfolio+wallet
        return total

    def plot(self, total):
        """
        Plot portfolio
        :param total: values over time
        :return:
        """
        # Plot two charts to assess trades and equity curve
        fig = plt.figure()
        fig.patch.set_facecolor('white')  # Set the outer colour to white
        # Plot the equity curve in dollars
        ax2 = fig.add_subplot(212, ylabel='Portfolio value in $')
        ax2.plot(self.strategy.times[self.strategy.signal_shift:], total, lw=2.)

        # Plot the "buy" and "sell" trades against the equity curve
        indices_buy = np.where(self.strategy.signal == 1)[0]
        ax2.plot(self.strategy.times[self.strategy.signal_shift:][indices_buy],
                 total[indices_buy],
                 '^', markersize=10, color='g')
        # Plot the "sell" trades against stock
        indices_sell = np.where(self.strategy.signal == -1)[0]
        ax2.plot(self.strategy.times[self.strategy.signal_shift:][indices_sell],
                 total[indices_sell],
                 'v', markersize=10, color='r')
        # Plot the figure
        fig.show()
