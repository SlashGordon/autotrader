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
from datetime import date, datetime
import numpy as np
from dateutil.relativedelta import relativedelta
from autotrader.filter.base_filter import BaseFilter


class StockIsHot(BaseFilter):
    """
    This filter creates with the help of multiple polyfits in an given date range
    a score for a stock. The value 1 is the best and 0 the worst.
    A stock with a score between 0.75 and 1. shows a good performance.
    """

    NAME = 'StockIsHot'

    def __init__(self, arguments: dict, logger: logging.Logger):
        self.buy = arguments['threshold_buy']
        self.sell = arguments['threshold_sell']
        self.lookback = arguments['lookback']
        self.intervals = arguments['intervals']
        super(StockIsHot, self).__init__(arguments, logger)

    def analyse(self):
        performance_list = []
        for intervals in self.intervals:
            performance_list.append(self.get_performance(self.bars[:, 1], intervals))

        ascending_counter = 0
        perf_sum = 0

        for idx, performance in enumerate(performance_list):
            for val in performance:
                perf_sum += (1.0 + idx*4)

                if val >= 0:
                    ascending_counter += (1.0 + idx*4)
        if perf_sum != 0:
            self.calc = (ascending_counter / perf_sum)
            self.logger.debug("Calculated performance is '%f'." % self.calc)
        else:
            self.logger.warning("Division by zero.")
            return BaseFilter.SELL

        if self.calc >= self.buy:
            return BaseFilter.BUY
        elif self.calc <= self.sell:
            return BaseFilter.SELL

        return BaseFilter.HOLD

    def get_calculation(self):
        return self.calc

    @staticmethod
    def get_performance(array, interval: int):
        """
        Splits values by interval and calculates for each split the performance value
        :param array: close prices of stock
        :param interval: interval in days
        :return: list with performance values
        """
        array = array[array != np.array(None)]
        steps = int(array.shape[0]/interval)
        delta_list = np.zeros(steps)
        for idx in range(1, steps+1):
            y_values = array[interval*idx-interval:interval*idx]
            x_values = np.arange(y_values.shape[0])
            poly = np.polyfit(x_values, y_values, 1)
            delta_list[idx-1] = poly[0]
        return np.diff(delta_list)

    def look_back_date(self):
        return datetime.today() + relativedelta(months=-self.lookback)
