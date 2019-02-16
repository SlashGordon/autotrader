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
import datetime
import logging

from autotrader.base.trader_base import TraderBase
from autotrader.datasource.database.stock_schema import BARS_NUMPY, Filter, Stock
from autotrader.filter.adx_filter import AdxFilter
from autotrader.filter.base_filter import BaseFilter
from autotrader.filter.rsi_filter import RsiFilter
from autotrader.filter.stock_is_hot import StockIsHot
from autotrader.filter.stock_is_hot_secure import StockIsHotSecure
from autotrader.filter.piotroski_score import PiotroskiScore
from autotrader.filter.levermann_score import LevermannScore
from autotrader.filter.price_target_score import PriceTargetScore


class BuildFilters:
    """
    This tool builds all filters
    """
    arguments_rsip14 = {
        'stock': None,
        'name': 'RsiP14',
        'bars': None,
        'threshold_buy': 70.0,
        'threshold_sell': 70.0,
        'parameter': 14,
        'lookback': 2
    }

    arguments_rsip5 = {
        'stock': None,
        'name': 'RsiP5',
        'bars': None,
        'threshold_buy': 70.0,
        'threshold_sell': 70.0,
        'parameter': 5,
        'lookback': 1
    }

    arguments_adxp14 = {
        'stock': None,
        'name': 'AdxP14',
        'bars': None,
        'threshold_buy': 30.0,
        'threshold_sell': 30.0,
        'parameter': 14,
        'lookback': 2
    }

    arguments_adxp5 = {
        'stock': None,
        'name': 'AdxP5',
        'bars': None,
        'threshold_buy': 30.0,
        'threshold_sell': 30.0,
        'parameter': 5,
        'lookback': 1
    }

    arguments_hot2 = {
        'stock': None,
        'name': 'StockIsHot2Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'lookback': 2
    }

    arguments_hot3 = {
        'stock': None,
        'name': 'StockIsHot3Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'lookback': 3
    }

    arguments_hot6 = {
        'stock': None,
        'name': 'StockIsHot6Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'lookback': 6
    }

    arguments_sec2 = {
        'stock': None,
        'name': 'SecureHot2Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'secure_value': 0.85,
        'lookback': 2
    }

    arguments_sec3 = {
        'stock': None,
        'name': 'SecureHot3Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'secure_value': 0.85,
        'lookback': 3
    }

    arguments_sec6 = {
        'stock': None,
        'name': 'SecureHot6Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'secure_value': 0.85,
        'lookback': 6
    }

    arguments_sech2 = {
        'stock': None,
        'name': 'SecureHotH2Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'secure_value': 1.2,
        'lookback': 2
    }

    arguments_sech3 = {
        'stock': None,
        'name': 'SecureHotH3Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'secure_value': 1.25,
        'lookback': 3
    }

    arguments_sech6 = {
        'stock': None,
        'name': 'SecureHotH6Month',
        'bars': None,
        'threshold_buy': 0.8,
        'threshold_sell': 0.5,
        'intervals': [7, 30],
        'secure_value': 1.3,
        'lookback': 6
    }

    arguments_pio = {
        'stock': None,
        'name': 'PiotroskiScore',
        'bars': None,
        'threshold_buy': 8,
        'threshold_sell': 5,
        'intervals': None,
        'lookback': None
    }

    arguments_lev = {
        'stock': None,
        'name': 'LevermannScore',
        'bars': None,
        'threshold_buy': 7,
        'threshold_sell': 2,
        'intervals': None,
        'lookback': 12
    }

    arguments_pri = {
        'stock': None,
        'name': 'PriceTargetScore',
        'bars': None,
        'threshold_buy': 8,
        'threshold_sell': -2,
        'intervals': None,
        'lookback': 2
    }

    def __init__(self, arguments: dict, logger: logging.Logger):
        self.db_tool = arguments["db_tool"]
        if "filters" in arguments:
            self.filters = arguments["filters"]
        else:
            self.filters = [
                AdxFilter(BuildFilters.arguments_adxp5, logger),
                AdxFilter(BuildFilters.arguments_adxp14, logger),
                RsiFilter(BuildFilters.arguments_rsip5, logger),
                RsiFilter(BuildFilters.arguments_rsip14, logger),
                StockIsHot(BuildFilters.arguments_hot2, logger),
                StockIsHot(BuildFilters.arguments_hot3, logger),
                StockIsHot(BuildFilters.arguments_hot6, logger),
                StockIsHotSecure(BuildFilters.arguments_sec2, logger),
                StockIsHotSecure(BuildFilters.arguments_sec3, logger),
                StockIsHotSecure(BuildFilters.arguments_sec6, logger),
                StockIsHotSecure(BuildFilters.arguments_sech2, logger),
                StockIsHotSecure(BuildFilters.arguments_sech3, logger),
                StockIsHotSecure(BuildFilters.arguments_sech6, logger),
                PiotroskiScore(BuildFilters.arguments_pio, logger),
                LevermannScore(BuildFilters.arguments_lev, logger),
                PriceTargetScore(BuildFilters.arguments_pri, logger)
            ]
        if 'stocks' in arguments:
            self.stocks = arguments["stocks"]
        else:
            self.db_tool.connect()
            self.stocks = self.db_tool.session.query(Stock).all()
        self.logger = logger

    def set_filters(self, filters):
        """
        Overwrite actual filter list
        :param filters: list with filters
        :return: nothing
        """
        self.filters = filters

    def build(self):
        """
        Starts the build process for given filters
        :return: nothing
        """
        rc = 0
        for stock in self.stocks:
            self.logger.info("Analyse %s:%s", stock.indices[0].symbol, stock.symbol)
            for my_filter in self.filters:
                try:
                    self.logger.info("Execute filter %s", my_filter.name)
                    self.__build(my_filter, stock)
                except TypeError:
                    self.logger.exception("Filter {} causes exceptions.".format(my_filter.name))
                    rc += 1
                except RuntimeError:
                    self.logger.exception("Filter {} causes exceptions.".format(my_filter.name))
        self.db_tool.commit()
        return rc

    def __build(self, my_filter, stock):
        bars = stock.get_bars(my_filter.look_back_date(), datetime.datetime.now(),
                              output_type=BARS_NUMPY)
        if my_filter.look_back_date() is None or bars.size:
            my_filter.set_bars(bars)
            my_filter.set_stock(stock)
            strategy_status = my_filter.analyse()
            strategy_value = my_filter.get_calculation()
            tz = TraderBase.get_timezone()
            stock.filter.append(
                Filter(
                    value=strategy_value,
                    name=my_filter.name,
                    status=strategy_status,
                    date=datetime.datetime.now(tz)
                )
            )
            if strategy_status == BaseFilter.BUY:
                self.logger.debug("Buy %s", stock.symbol)
            elif strategy_status == BaseFilter.HOLD:
                self.logger.debug("Hold %s", stock.symbol)
            else:
                self.logger.debug("Do not buy Stock %s ", stock.symbol)
