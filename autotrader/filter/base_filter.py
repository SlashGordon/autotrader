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


class BaseFilter:
    """
    Base Class for autotrader filter
    """

    SELL = 0
    BUY = 1
    HOLD = 2

    def __init__(self, arguments, logger: logging.Logger):
        self.logger = logger
        self.stock = arguments['stock']
        self.name = arguments['name']
        self.bars = arguments['bars']
        self.calc = 0

    def analyse(self):
        """
        Starts analysis process
        :return:
        """
        raise NotImplementedError

    def get_calculation(self):
        """
        Returns the calculation of analysis
        :return: calculated value
        """
        raise NotImplementedError

    def look_back_date(self):
        """
        Returns the look back date
        :return: look back in months
        """
        raise NotImplementedError

    def set_bars(self, bars):
        """
        Setter method for bar
        :param bars:
        :return: nothing
        """
        self.bars = bars

    def set_stock(self, stock):
        """
        Setter for stock
        :param stock: sqlalchemy object
        :return: nothing
        """
        self.stock = stock
