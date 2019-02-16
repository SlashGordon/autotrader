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
from datetime import datetime, timedelta
from autotrader.datasource.database.stock_schema import BARS_NUMPY


class BuildIndicatorsBase:
    """
    A base class for a Tool to build indicators with optimized arguments.
    """

    def __init__(self, config, arguments, logger: logging.Logger):
        self.signal_to_builds = arguments['signals']
        self.look_back = arguments['look_back']
        self.stock_ids = None if "ALL" in arguments['stocks'] else arguments['stocks']
        self.config = config
        self.logger = logger
        self.client = None
        self.arguments = arguments
        self.bulk_data_storage = {
            "parameter": [],
            "plot": [],
            "plot_create": [],
            "signal": []
        }

    def work_generator(self):
        """

        :return:
        """
        raise NotImplementedError

    def commit_work_result(self):
        """

        :return:
        """
        raise NotImplementedError

    def build(self):
        """
        Start indicator build in serial mode
        :return:
        """
        return_code = 0
        self.logger.info("Start indicator build in serial mode")
        for arguments in self.work_generator():
            return_code += self.build_indicator(arguments)
        self.commit_work_result()
        return return_code

    def build_indicator(self, arguments):
        """

        :param arguments: dictionary with arguments
        :return:
        """
        raise NotImplementedError

    def get_last_known_value(self, stock):
        """
        Returns last known value of stock
        :param stock:
        :return:
        """
        raise NotImplementedError

    def get_real_time_series(self, issue_id):
        """
        Returns last known series of stock
        :param issue_id:
        :return:
        """
        raise NotImplementedError

    def get_bars(self, stock, data_size_days):
        if stock and data_size_days:
            return stock.get_bars(
                start=datetime.now() + timedelta(days=-data_size_days),
                end=datetime.now(),
                output_type=BARS_NUMPY
            )
        return None

