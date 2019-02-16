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
import tulipy as ti
from dateutil.relativedelta import relativedelta
from autotrader.filter.base_filter import BaseFilter


class RsiFilter(BaseFilter):
    """
    The RSI Filter says trust other indicators
    when threshold of 70 have been reached.
    """

    NAME = 'AdxFilter'

    def __init__(self, arguments: dict, logger: logging.Logger):
        self.buy = arguments['threshold_buy']
        self.sell = arguments['threshold_sell']
        self.lookback = arguments['lookback']
        self.parameter = arguments['parameter']
        super(RsiFilter, self).__init__(arguments, logger)

    def analyse(self):

        close = self.bars[:, 0].copy(order='C').astype('float64')
        if not (close.size - self.parameter > 0):
            raise RuntimeError
        my_result = ti.rsi(close, self.parameter)
        median = np.median(my_result)
        if not np.isnan(median):
            self.calc = float(median)
        else:
            self.logger.warning("Data causes nan. {}".format(close))
        if self.calc >= self.buy:
            return BaseFilter.BUY
        elif self.calc <= self.sell:
            return BaseFilter.SELL

        return BaseFilter.HOLD

    def get_calculation(self):
        return self.calc

    def look_back_date(self):
        return datetime.today() + relativedelta(months=-self.lookback)
