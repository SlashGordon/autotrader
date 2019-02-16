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
import itertools
import logging
import datetime

from autotrader.base.trader_base import TraderBase

from autotrader.broker.degiro.degiro_client import DegiroClient
from autotrader.datasource.database.stock_schema import Signal, Parameter, Plot, Stock
import autotrader.indicators as ind
from autotrader.tool.indicators.build_indicators_base import BuildIndicatorsBase
from autotrader.tool.indicators.optimizer import Optimizer


class BuildIndicators(BuildIndicatorsBase):
    """
    Tool to build indicators with optimized arguments from the scratch.
    """

    def __init__(self, config, arguments, logger: logging.Logger):
        super(BuildIndicators, self).__init__(config, arguments, logger)
        self.client = DegiroClient(config['degiro'], {"db_tool": None}, self.logger)

    def build_indicator(self, arguments):
        stock_id = arguments["stock_id"]
        stock_index = arguments["stock_index"]
        stock_symbol = arguments["stock_symbol"]
        stock_bars = arguments["stock_bars"]
        self.logger.info("Analyse %s:%s" % (stock_index, stock_symbol))
        return_code = 0
        indicators = []
        for indicator in ind.INDICATORS:
            if indicator.SHORT_NAME in self.signal_to_builds or 'ALL' in self.signal_to_builds:
                indicators.append(indicator(indicator.ARGUMENTS, self.logger))

        for indicator in indicators:
            self.logger.info("Execute filter %s" % indicator.name)
            if indicator.SHORT_NAME in ["SO", "SOM2", "SOM3"]:
                optimizer_values = itertools.product(
                    range(3, int(self.look_back/2)),
                    range(3, int(self.look_back/2)),
                    range(3, int(self.look_back/2))
                )
            else:
                optimizer_values = itertools.combinations(
                    range(5, int(self.look_back/2)),
                    indicator.param_count
                )
            profit_max, param_max, status = Optimizer(self.logger).run_optimizer(
                optimizer_values, indicator, stock_bars)
            self.logger.info("Signal %s(%s) earns %s for %s and has status code %s" %
                             (indicator.name, param_max, profit_max, stock_symbol, status))
            if not param_max:
                self.logger.warning("no results for %s", indicator)
                continue
            # save to bulk data storage
            db_signal = Signal(
                profit_in_percent=float(profit_max),
                name=indicator.name,
                status=status,
                info=self.look_back,
                date=datetime.datetime.now(TraderBase.get_timezone()),
                refresh_date=datetime.datetime.now(TraderBase.get_timezone())
                )
            self.__add_signal_to_bulk(stock_id, db_signal)
            self.__add_parameter_to_bulk(db_signal, param_max)
            self.__add_plot_to_bulk(indicator, param_max, db_signal)
        return return_code

    def get_last_known_value(self, stock):
        raise NotImplementedError

    def get_real_time_series(self, issue_id):
        raise NotImplementedError

    def __add_parameter_to_bulk(self, my_signal, my_parameters):
        """
        Add parameter to bulk data storage

        :param my_signal: signal belongs to parameter
        :param my_parameters: list of parameters

        :return: false if operation fails otherwise true
        """
        if my_signal and my_parameters:
            for para in my_parameters:
                my_param = Parameter(
                    value=para
                )
                my_signal.parameter.append(
                    my_param
                )
                self.bulk_data_storage["parameter"].append(my_param)
            return True
        return False

    def __add_plot_to_bulk(self, my_strategy, my_param, my_signal):
        """
        Add plot to bulk data storage
        :param my_strategy:
        :param my_param:
        :param my_signal:
        :return:
        """
        if my_strategy and my_param and my_signal:
            my_strategy.set_parameters(my_param)
            my_plot = Plot(
                data=my_strategy.get_plot()
            )
            my_signal.plot.append(
                my_plot
            )
            self.bulk_data_storage["plot"].append(my_plot)
            return True
        return False

    def __add_signal_to_bulk(self, my_stock_id, my_signal):
        """
        Add plot to bulk data storage
        :param my_signal:
        :param my_stock_id: stock id of stock that belongs to signal
        :return: false if operation fails otherwise true
        """
        if my_stock_id and my_signal:
            self.bulk_data_storage["signal"].append([my_stock_id, my_signal])
            return True
        return False

    def __fix_relationships(self, stocks):
        my_signals = []
        for stock in stocks:
            for my_signal in self.bulk_data_storage["signal"]:
                if len(my_signal) == 2 and stock.id == my_signal[0]:
                    stock.signal.append(my_signal[1])
                    my_signals.append(my_signal[1])
        self.bulk_data_storage["signal"] = my_signals

    def work_generator(self):
        """

        :return:
        """
        db_tool = self.arguments["db_tool"]

        stocks = db_tool.session.query(Stock).filter(Stock.id.in_(self.stock_ids)).all() \
            if self.stock_ids else db_tool.session.query(Stock).all()

        self.arguments["stocks"] = stocks
        for stock in stocks:
            my_bars = self.get_bars(stock, self.look_back)
            if my_bars is not None and hasattr(my_bars, 'shape') and len(my_bars.shape) >= 2 and my_bars.shape[1] == 6:
                yield {
                    "stock_id": stock.id,
                    "stock_index": stock.indices[0],
                    "stock_symbol": stock.symbol,
                    "stock_bars": my_bars
                }
            else:
                self.logger.warning('Skip indicator build for {} because of missing bars.'.format(stock.symbol))

    def commit_work_result(self):
        """

        :return:
        """
        db_tool = self.arguments["db_tool"]
        stocks = self.arguments["stocks"]
        self.__fix_relationships(stocks)
        db_tool.session.add_all(self.bulk_data_storage["signal"])
        db_tool.session.add_all(self.bulk_data_storage["parameter"])
        db_tool.session.add_all(self.bulk_data_storage["plot"])
        db_tool.commit()
