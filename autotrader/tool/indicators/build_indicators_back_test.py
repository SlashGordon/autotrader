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
from datetime import date, datetime, timedelta
from autotrader.tool.indicators.build_indicators_quick import BuildIndicatorsQuick
from autotrader.datasource.database.stock_schema import BARS_NUMPY, Stock, LookupTable


class BuildIndicatorsBackTest(BuildIndicatorsQuick):
    """
    Tool to refresh the status of existing indicators.
    """

    def __init__(self, config, arguments, logger: logging.Logger):
        super(BuildIndicatorsBackTest, self).__init__(config, arguments, logger)

    def get_real_time_series(self, issue_id):
        """
        Returns real time series depended of using mode
        :param self:
        :param issue_id:
        :return:
        """
        db_tool = self.arguments["db_tool"]
        stock = db_tool.session.query(LookupTable).\
            filter(LookupTable.lookup_id == issue_id).first().stock
        return stock.get_bars(datetime.combine(date.today(), datetime.min.time()),
                              datetime.combine(date.today(), datetime.max.time()))

    def get_bars(self, stock, data_size_days):
        if stock and data_size_days:
            my_bars = stock.get_bars(
                start=datetime.now() + timedelta(days=-data_size_days),
                end=datetime.now() + timedelta(days=-1),
                output_type=BARS_NUMPY
            )
            return my_bars
        return None

