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

from autotrader.datasource.database.stock_schema import OrderType, Portfolio, Orders
from autotrader.strategy.strategy_base import StrategyBase as Dsm
from autotrader.strategy.strategy_filter import StrategyFilter as Sf


class StartStrategy:
    """
    Start all strategies
    """

    strategies = [
        {
            "strategy": "SimpleMarket40",  # Name of portfolio
            "class": Dsm,  # strategy class
            "cash": 2000,  # initial cash of strategy
            "buy_percentage": 0.4,  # buys stocks depended on your cash amount
            "sell_percentage": 1.,  # sells n percent of stock amount
            "order_type": OrderType.market  # order type of strategy
        },
        {
            "strategy": "SimpleLimit40",
            "class": Dsm,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "buy_under_value_limit_percentage": 0.01,
            "sell_over_value_limit_percentage": 0.005,
            "order_type": OrderType.limit
        },
        {
            "strategy": "RsiP14",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 70.0,
            "filter_name": "RsiP14",
            "ignore_signals": ["AroonSignal"],
            "order_type": OrderType.market
        },
        {
            "strategy": "RsiP5",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 70.0,
            "filter_name": "RsiP5",
            "ignore_signals": ["AroonSignal"],
            "order_type": OrderType.market
        },
        {
            "strategy": "AdxP14",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 30.0,
            "filter_name": "AdxP14",
            "ignore_signals": ["AroonSignal"],
            "order_type": OrderType.market
        },
        {
            "strategy": "AdxP5",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 30.0,
            "filter_name": "AdxP5",
            "ignore_signals": ["AroonSignal"],
            "order_type": OrderType.market
        },
        {
            "strategy": "RsiP14L",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 70.0,
            "filter_name": "RsiP14",
            "ignore_signals": ["AroonSignal"],
            "buy_under_value_limit_percentage": 0.002,
            "sell_over_value_limit_percentage": 0.002,
            "order_type": OrderType.limit
        },
        {
            "strategy": "RsiP5L",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 70.0,
            "filter_name": "RsiP5",
            "ignore_signals": ["AroonSignal"],
            "buy_under_value_limit_percentage": 0.002,
            "sell_over_value_limit_percentage": 0.002,
            "order_type": OrderType.limit
        },
        {
            "strategy": "AdxP14L",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 30.0,
            "filter_name": "AdxP14",
            "ignore_signals": ["AroonSignal"],
            "buy_under_value_limit_percentage": 0.002,
            "sell_over_value_limit_percentage": 0.002,
            "order_type": OrderType.limit
        },
        {
            "strategy": "AdxP5L",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 30.0,
            "filter_name": "AdxP5",
            "ignore_signals": ["AroonSignal"],
            "buy_under_value_limit_percentage": 0.002,
            "sell_over_value_limit_percentage": 0.002,
            "order_type": OrderType.limit
        },
        {
            "strategy": "SecureHot2Month",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.8,
            "filter_name": "SecureHot2Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHot3Month",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.7,
            "filter_name": "SecureHot3Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHot6Month",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.6,
            "filter_name": "SecureHot6Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHotH2Month",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.8,
            "filter_name": "SecureHotH2Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHotH3Month",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.7,
            "filter_name": "SecureHotH3Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHotH6Month",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.6,
            "filter_name": "SecureHotH6Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHotH6MonthL",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.6,
            "filter_name": "SecureHotH6Month",
            "buy_under_value_limit_percentage": 0.002,
            "sell_over_value_limit_percentage": 0.002,
            "order_type": OrderType.limit
        },
        {
            "strategy": "SecureHotH6NoAr",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.6,
            "ignore_signals": ["AroonSignal"],
            "filter_name": "SecureHotH6Month",
            "order_type": OrderType.market
        },
        {
            "strategy": "SecureHotH6NoArL",
            "class": Sf,
            "cash": 2000,
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "threshold": 0.6,
            "ignore_signals": ["AroonSignal"],
            "filter_name": "SecureHotH6Month",
            "buy_under_value_limit_percentage": 0.002,
            "sell_over_value_limit_percentage": 0.002,
            "order_type": OrderType.limit
        }
    ]

    def __init__(self, config, arguments: dict, logger: logging.Logger):
        self.logger = logger
        self.config = config
        self.db_tool = arguments["db_tool"]
        self.strategies_to_build = arguments["strategies"]
        self.strategy_name_prefix = arguments["strategy_name_prefix"]
        self.broker = arguments["broker"]

    def build(self):
        """
        Starts strategies
        :return:
        """
        return_code = 0
        all_strategies = self.get_all_strategies()
        for strategy in all_strategies:
            if "ALL" in self.strategies_to_build or \
                    strategy['strategy'] in self.strategies_to_build:
                strategy_name = self.strategy_name_prefix + strategy['strategy']
                try:
                    self.broker.set_portfolio(strategy_name, "user", strategy["cash"])
                    simple_market = strategy["class"](self.config, strategy, self.broker,
                                                      self.logger)
                    simple_market.start_strategy(True, True)
                except RuntimeError:
                    self.logger.exception("Error during {}".format(strategy_name))
                    return_code += 1

        return return_code

    def recreate_all_strategies(self):
        """
        Recreates all strategies i.e. all orders of an existing portfolio will be deleted.
        :return:
        """
        # subquery doesn't work for inane reason
        delete_portfolio = self.broker.db_tool.session.query(Portfolio.id) \
            .filter(Portfolio.name.startswith(self.strategy_name_prefix)).all()
        delete_portfolio = [port_id[0] for port_id in delete_portfolio]
        if delete_portfolio:
            self.db_tool.session.query(Orders) \
                .filter(Orders.orders_id > 0) \
                .filter(Orders.portfolio_id.in_(delete_portfolio)) \
                .delete(synchronize_session='fetch')
            self.db_tool.session.query(Orders) \
                .filter(Orders.portfolio_id.in_(delete_portfolio)) \
                .delete(synchronize_session='fetch')
            self.db_tool.session.query(Portfolio) \
                .filter(Portfolio.id.in_(delete_portfolio)) \
                .delete(synchronize_session='fetch')

    @staticmethod
    def __extend_strategies(strategies, strategy_sufix, key, param_list):
        extended_strategies = []
        for param in param_list:
            new_strategies = []
            for strategy in strategies:
                new_strategy = dict(strategy)
                new_strategy['strategy'] = new_strategy['strategy'] + strategy_sufix\
                    + str(int(param*100))
                new_strategy[key] = param
                new_strategies.append(new_strategy)
            extended_strategies += new_strategies
        return extended_strategies

    def get_all_strategies(self):
        """
        Return all strategies + dynamic created strategies
        :return:
        """
        my_stock_is_hot = [stock_is_hot for stock_is_hot in StartStrategy.strategies
                           if stock_is_hot["strategy"] in ["StockIsHot6Month", "SecureHotH2Month",
                                                           "SecureHotH3Month", "SecureHotH6Month"]]
        all_strategies = self.__extend_strategies(my_stock_is_hot, "T", "threshold",
                                                  [.4, .5, .6, .65, .7, .75, .8, .85, .9, .95])
        all_strategies += self.__extend_strategies(all_strategies, "V", "buy_threshold",
                                                   [.4, .5, .6, .7, .75, .8, .85, .9, .95])
        all_strategies += self.__extend_strategies(StartStrategy.strategies, "V", "buy_threshold",
                                                   [0.3, .4, .5, .6, .7])
        all_strategies += StartStrategy.strategies
        # create aroon strategies
        #filtered_dict = copy.deepcopy([k for k in all_strategies if k["class"] == Sf])
        #for item in filtered_dict:
        #    item["strategy"] += "Ar"
        #    item["class"] = Sos
        #    item["signal_name"] = "AroonSignal"

        # all_strategies += filtered_dict
        return all_strategies
