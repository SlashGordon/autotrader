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

import autotrader.indicators as ind
from autotrader.datasource.database.stock_schema import Signal, Orders, Plot, Stock
from autotrader.base.trader_base import TraderBase
from autotrader.broker.degiro.degiro_client import DegiroClient
from autotrader.tool.indicators.build_indicators_base import BuildIndicatorsBase
from autotrader.tool.indicators.optimizer import Optimizer


class BuildIndicatorsQuick(BuildIndicatorsBase):
    """
    Tool to refresh the status of existing indicators.
    """

    def __init__(self, config, arguments, logger: logging.Logger):
        super(BuildIndicatorsQuick, self).__init__(config, arguments, logger)
        self.client = None
        if 'offline' not in arguments:
            self.client = DegiroClient(config['degiro'], {"db_tool": None}, self.logger)
        if 'signal_max_age' not in arguments:
            self.arguments['signal_max_age'] = 6

    def work_generator(self):
        """

        :return:
        """
        db_tool = self.arguments["db_tool"]
        stocks = db_tool.session.query(Stock).filter(Stock.id.in_(self.stock_ids)).all() \
            if self.stock_ids else db_tool.session.query(Stock).all()
        new_signals = self.__get_signals_to_update(db_tool, self.arguments["signal_max_age"])

        self.arguments["signals"] = new_signals
        self.arguments["stocks"] = stocks
        for stock in stocks:
            my_bars = self.get_bars(stock, self.look_back)
            if my_bars is not None and hasattr(my_bars, 'shape') and len(my_bars.shape) >= 2 and my_bars.shape[1] == 6:
                yield {
                    "stock_id": stock.id,
                    "stock_index": stock.indices[0],
                    "stock_issue_id": stock.get_degiro_id(),
                    "stock_symbol": stock.symbol,
                    "update_new_signals": [[sig, sig.plot[0].id if sig.plot else None]
                                           for sig in new_signals
                                           if sig.stock_id == stock.id],
                    "stock_bars": my_bars
                }
            else:
                self.logger.warning('Skip indicator build for {} because of missing bars.'.format(stock.symbol))

    def commit_work_result(self):
        """

        :return:
        """
        db_tool = self.arguments["db_tool"]
        if db_tool is None:
            raise RuntimeError("DB tool is not initialized")
        db_tool.session.bulk_update_mappings(Signal, self.bulk_data_storage["signal"])
        if self.bulk_data_storage["plot"]:
            db_tool.session.bulk_update_mappings(Plot, self.bulk_data_storage["plot"])
        if "plot_create" in self.bulk_data_storage:
            db_tool.session.bulk_insert_mappings(Plot, self.bulk_data_storage["plot_create"])
        db_tool.commit()

    def build_indicator(self, arguments):
        stock_issue_id = arguments["stock_issue_id"]
        update_new_signals = arguments["update_new_signals"]
        stock_symbol = arguments["stock_symbol"]
        stock_bars = arguments["stock_bars"]
        return_code = 0
        if not update_new_signals:
            self.logger.warning("No update able signals found for %s" % stock_symbol)
            return 0
        # select signals to refresh only new and used signals by orders will be refreshed
        # the date filter with datetime.now() is necessary for backtesting
        self.logger.info("Analyse %s" % stock_symbol)
        # get live data
        real_time_value = self.get_last_known_value(stock_issue_id)
        if real_time_value is None:
            self.logger.warning("Can not calculate indicators for {} because of missing"
                                " real time data. Date is {} and weekday is {}".
                                format(stock_symbol, datetime.now(),
                                       datetime.now().strftime('%A')))
            return 0

        indicators = []
        for indicator in ind.INDICATORS:
            indicators.append(indicator(indicator.ARGUMENTS, self.logger))

        for indicator in indicators:
            self.logger.info("Execute filter %s" % indicator.name)
            for update_new_signal in update_new_signals:
                signal_to_update = update_new_signal[0]
                plot_to_update = update_new_signal[1]
                if indicator.NAME != signal_to_update.name:
                    continue
                indicator.set_bars(stock_bars)
                optimizer_values = [[x.value for x in signal_to_update.parameter]]
                profit_max, param_max, status = Optimizer(self.logger).run_optimizer(
                    optimizer_values, indicator, stock_bars, real_time_value)
                # save to database
                indicator.set_parameters(param_max)
                self.bulk_data_storage["signal"].append(
                    {"id": signal_to_update.id,
                     "refresh_date": datetime.now(),
                     "profit_in_percent": float(profit_max),
                     "status": status
                     }
                )
                if plot_to_update:
                    self.bulk_data_storage["plot"].append(
                        {
                            "id": plot_to_update,
                            "data": indicator.get_plot(),
                            "signal_id": signal_to_update.id
                        }
                    )
                else:
                    self.bulk_data_storage["plot_create"].append(
                        {
                            "data": indicator.get_plot(),
                            "signal_id": signal_to_update.id
                        }
                    )
        return return_code

    def get_last_known_value(self, issue_id):
        real_time_series = self.get_real_time_series(issue_id)
        if real_time_series:
            if len(real_time_series) == 1 and real_time_series[0].date.date() > \
                    datetime.now().date():
                # this is only possible in back test mode
                return real_time_series[0]
            for realtime_value in real_time_series:
                if datetime.now().date() == realtime_value.date.date():
                    return realtime_value
        return None

    def get_real_time_series(self, issue_id):
        """
        Returns real time series depended of using mode
        :param self:
        :param issue_id:
        :return:
        """
        return self.client.get_day(issue_id)

    @staticmethod
    def __get_signals_to_update(db_tool, signal_max_age):
        time_zone = TraderBase.get_timezone()
        # at first we need all signals in a date range of 6 days
        all_signals_in_date_range = db_tool.session.query(Signal).\
            filter(Signal.date.between(datetime.now(time_zone) - timedelta(days=signal_max_age),
                                       datetime.now(time_zone)))

        # older signals connected with a order must also be refreshed
        sub_orders = db_tool.session.query(
            Orders.signal_id
        )\
            .filter(Orders.is_sell == 0)\
            .filter(Orders.orders_id.is_(None))\
            .group_by(Orders.signal_id).\
            subquery('t3')

        signals_with_order = db_tool.session.query(Signal).join(
            sub_orders,
            Signal.id == sub_orders.c.signal_id
        )
        update_new_signals = all_signals_in_date_range.union_all(signals_with_order)
        my_result = update_new_signals.all()
        return my_result
