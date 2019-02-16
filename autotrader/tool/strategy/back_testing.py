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
from datetime import timedelta
from freezegun import freeze_time
from autotrader.tool.indicators.build_indicators_back_test import BuildIndicatorsBackTest
from autotrader.tool.strategy.start_strategy import StartStrategy


class BackTestingStrategy:
    """
    Back test all strategies
    """

    def __init__(self, config, arguments, logger: logging.Logger):
        self.logger = logger
        self.config = config
        self.arguments = arguments
        self.db_tool = self.arguments["db_tool"]

    @staticmethod
    def date_range(start_date, end_date):
        """
        This method iterates from start to end date with 1 day increment and skips
        the weekend dates.
        :param start_date:
        :param end_date:
        :return: a datetime object
        """
        if start_date is None or end_date is None:
            return None
        all_days = int((end_date - start_date).days)
        for n in range(all_days + 1):
            new_date = start_date + timedelta(n)
            if new_date.isoweekday() in range(1, 6):
                yield new_date.replace(hour=9, minute=35)

    def build(self):
        """

        :return:
        """
        exit_code = 0
        # find earliest signal and use signal date to travel in the past
        self.db_tool.connect()
        # delete all old orders and recreate portfolios
        arguments_strategy = {
            'strategies': "{}".format(self.arguments["strategies"]),
            'broker': self.arguments["broker"],
            'strategy_name_prefix': 'B',
            'db_tool': self.db_tool
        }
        strategy_tool = StartStrategy(self.config, arguments_strategy, self.logger)
        strategy_tool.recreate_all_strategies()
        from_date = self.arguments["from_date"]
        to_date = self.arguments["to_date"]
        if from_date and to_date:
            for single_date in BackTestingStrategy.date_range(from_date, to_date):
                exit_code += self.build_with_date(single_date, strategy_tool)
        return exit_code

    def build_with_date(self, my_date, strategy_tool):
        """
        Execute build and indicator quick build by date
        :param my_date: start date
        :param strategy_tool:
        :return:
        """
        exit_code = 0
        with freeze_time(my_date):
            if my_date.weekday() == 0:
                self.arguments["broker"].commit_work()
            self.logger.debug("Date is set to %s" % my_date)
            # start to refresh signal
            arguments = {
                'signals': self.arguments["signals"],
                'stocks': self.arguments["stocks"],
                'look_back': 300,
                'signal_max_age': 300,
                'db_tool': self.db_tool
            }
            exit_code += BuildIndicatorsBackTest(self.config, arguments, self.logger).build()
            # start strategies
            exit_code += strategy_tool.build()
        return exit_code
