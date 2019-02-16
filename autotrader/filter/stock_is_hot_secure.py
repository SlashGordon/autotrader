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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from autotrader.filter.base_filter import BaseFilter
from autotrader.filter.stock_is_hot import StockIsHot


class StockIsHotSecure(StockIsHot):
    """
    This filter creates with the help of multiple polyfits in an given date range
    a score for a stock. The value 1 is the best and 0 the worst.
    A stock with a score between 0.75 and 1. shows a good performance.
    """

    NAME = 'StockIsHotSecure'

    def __init__(self, arguments: dict, logger: logging.Logger):
        self.secure_value = arguments["secure_value"]
        super(StockIsHotSecure, self).__init__(arguments, logger)

    def analyse(self):
        first_value = self.bars[:, 1][0]
        last_value = self.bars[:, 1][-1]
        if first_value == 0:
            return BaseFilter.HOLD
        secure_value = last_value/first_value
        # The stock shows strong losses over a longer period of time. So we decrease the score.
        self.bars = self.bars[:][int(len(self.bars) / 2):]
        status = super(StockIsHotSecure, self).analyse()
        if secure_value > self.secure_value:
            return status
        self.calc = self.calc/2
        if self.calc >= self.buy:
            return BaseFilter.BUY
        elif self.calc <= self.sell:
            return BaseFilter.SELL
        return BaseFilter.HOLD

    def look_back_date(self):
        return datetime.today() + relativedelta(months=-self.lookback*2)
