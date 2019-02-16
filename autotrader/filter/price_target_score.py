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

from dateutil.relativedelta import relativedelta

from autotrader.filter.base_filter import BaseFilter


class PriceTargetScore(BaseFilter):
    """
    Price target score filter
    """

    NAME = 'PriceTargetScore'

    def __init__(self, arguments: dict, logger: logging.Logger):
        self.buy = arguments['threshold_buy']
        self.sell = arguments['threshold_sell']
        self.lookback = arguments['lookback']
        self.intervals = arguments['intervals']
        super(PriceTargetScore, self).__init__(arguments, logger)

    def analyse(self):
        price_target_score = 0
        try:
            prices = self.stock.get_data("recommendation")['priceTarget']
            low = float(prices['low'])
            high = float(prices['high'])
            mean = float(prices['mean'])
            current = self.bars[:, 0][-1]
            diff_low = current - low
            diff_high = current - high
            diff_mean = current - mean
            low_steps = (mean - low) / 10.0
            if low_steps == 0:
                low_steps = 1
            high_steps = (high - mean) / 10.0
            if high_steps == 0:
                high_steps = 1
            if diff_low < 0:
                price_target_score = -1 * abs(int(diff_low/low_steps))
            elif diff_high > 0:
                price_target_score = int(diff_high / high_steps)
            elif diff_mean < 0:
                price_target_score = -1 * abs(int(diff_mean*2 / (low_steps+high_steps)))
            else:
                price_target_score = int(diff_mean*2 / (low_steps+high_steps))
            self.calc = price_target_score
        except KeyError:
            self.logger.exception("Error during calculation.")
        if self.calc >= self.buy:
            return BaseFilter.BUY
        elif self.calc <= self.sell:
            return BaseFilter.SELL

        return BaseFilter.HOLD

    def get_calculation(self):
        return self.calc

    def look_back_date(self):
        return datetime.today() + relativedelta(months=-self.lookback)
