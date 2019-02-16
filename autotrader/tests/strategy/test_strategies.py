# -*- coding: utf-8 -*-
""" Autotrader

 Copyright 2017-2017 Slash Gordon

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
import os
import unittest
import datetime
from freezegun import freeze_time

from autotrader.filter.levermann_score import LevermannScore
from autotrader.filter.piotroski_score import PiotroskiScore
from autotrader.base.trader_base import TraderBase
from autotrader.broker.demo_broker import DemoBroker
from autotrader.datasource.database.stock_schema import Stock, Signal, Orders, OrderType, Status, \
    Filter, Parameter, Plot, BARS_NUMPY, Portfolio
from autotrader.tool.strategy.start_strategy import StartStrategy
from autotrader.tool.strategy.back_testing import BackTestingStrategy
from autotrader.strategy.strategy_base import StrategyBase as Dsm
from autotrader.strategy.strategy_filter import StrategyFilter as Sf
from autotrader.strategy.strategy_one_signal import StrategyOneSignal as Sos
from autotrader.strategy.strategy_signal_filter import StrategyFilterSignal as Sfs
from autotrader.strategy.strategy_group import StrategyGroup as Sg
from autotrader.datasource.database.stock_database import StockDataBase as Db
from autotrader.indicators.averages.moving_average_cross_signal import MovingAverageCrossSignal


class TestStrategies(unittest.TestCase):
    """
    Tests the demo simple market strategy
    """

    stock_list = [20, 3, 24, 2]

    @classmethod
    def setUpClass(cls):
        """
        create test basics
        :return:
        """
        cls.config = TraderBase.get_config()
        cls.test_logger = logging.getLogger()
        cls.test_logger.setLevel(logging.WARNING)
        cls.db_tool = Db(cls.config['sql'], cls.test_logger)
        cls.db_tool.connect()
        cls.portfolio_name = "TestDemoSimpleMarket"
        arguments_broker = {
            "portfolio_name": cls.portfolio_name,
            "portfolio_user": "user",
            "database_data": True,
            "db_tool": cls.db_tool,
            "cash": 20000000
        }
        cls.broker = DemoBroker(cls.config, arguments_broker, cls.test_logger)
        assert 'PYCHARM' in os.environ or cls.config['sql']['address'] == 'mysqltest'

    @classmethod
    def tearDownClass(cls):
        cls.db_tool.session = None

    def setUp(self):
        self.delete_all()
        self.broker.set_portfolio(self.portfolio_name, "user", 50000)
        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "order_type": OrderType.market
        }

        self.strategy = Dsm(self.config, arguments_strategy, self.broker, self.test_logger)

    def tearDown(self):
        self.delete_all()

    @freeze_time("2017-10-02")
    def test0_sell_signal(self):
        """
        the sell signal_id must always match with the buy signal id.
        """
        stocks = [1]
        days = [1, 5, 7, 10]
        fake_signals_name = ["FakeSignal1", "FakeSignal2", "FakeSignal3", "FakeSignal4"]
        fake_signals = []
        for idx, day in enumerate(days):
            with freeze_time(datetime.datetime.now(), + datetime.timedelta(days=day)):
                fake_signals.append(self.create_fake_signals(2, datetime.datetime.now(), stocks,
                                                             fake_signals_name[idx])[0])
                self.strategy.start_strategy(buy=True, sell=False)
            with freeze_time(datetime.datetime.now(), + datetime.timedelta(days=day,hours=2)):
                self.set_fake_signals(datetime.datetime.now(), -2, fake_signals_name[idx])
                self.strategy.start_strategy(buy=False, sell=True)
        self.broker.commit_work()
        my_orders = self.strategy.broker.db_tool.session.query(Orders).order_by(Orders.date).all()
        assert len(fake_signals) == len(fake_signals_name)
        assert len(my_orders) == len(fake_signals_name) * 2
        # compare the signal ids
        for idx, fake_signal in zip(range(0, len(fake_signals), 2), fake_signals):
            assert my_orders[idx].signal_id == fake_signal.id
            assert my_orders[idx+1].signal_id == fake_signal.id

    @freeze_time("2017-10-02")
    def test1_buy_market(self):
        """
        Checks if strategy buy.
        """
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.db_tool.commit()
        self.strategy.start_strategy(buy=True, sell=False)
        self.broker.refresh()
        portfolio = self.broker.get_portfolio_items()
        assert portfolio
        assert len(portfolio) == len(self.stock_list)
        for item in portfolio:
            assert item['stock_id'] in self.stock_list

    @freeze_time("2017-10-09")
    def test2_sell_market(self):
        """
        Checks if strategy sell
        """
        self.test1_buy_market()
        self.set_fake_signals(datetime.datetime.now())
        portfolio = self.broker.get_portfolio_items()
        assert portfolio
        self.strategy.start_strategy(buy=False, sell=True)
        portfolio = self.broker.get_portfolio_items()
        self.broker.commit_work()
        my_orders_all = self.db_tool.session.query(Orders).all()
        my_orders = self.db_tool.session.query(Orders).filter(Orders.orders_id >= 0).all()
        assert len(my_orders)*2 == len(my_orders_all)
        for my_order in my_orders:
            my_order_ass = self.db_tool.session.query(Orders). \
                filter(my_order.orders_id == Orders.id).first()
            assert my_order.stock_id == my_order_ass.stock_id
            assert my_order.signal_id == my_order_ass.signal_id
            assert my_order.size == abs(my_order_ass.size)
            assert my_order.portfolio_id == my_order_ass.portfolio_id
            assert my_order.id != my_order_ass.id
        assert not portfolio

    @freeze_time("2017-10-09")
    def test3_money_problems_market(self):
        """
        test buy if not enough money
        :return:
        """
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        arguments_broker = {
            "portfolio_name": "30Bugs",
            "portfolio_user": "user",
            "database_data": True,
            "db_tool": self.db_tool,
            "cash": 200000
        }
        broker = DemoBroker(self.config, arguments_broker, self.test_logger)
        broker.delete_portfolio(arguments_broker["portfolio_name"], "user")
        broker.set_portfolio(arguments_broker["portfolio_name"], "user", 30)
        arguments_strategy = {
            "buy_percentage": 1.,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": .005,
            "order_type": OrderType.market
        }
        strategy = Dsm(self.config, arguments_strategy, broker, self.test_logger)
        self.db_tool.commit()
        strategy.start_strategy(buy=True, sell=False)
        broker.refresh()
        portfolio = self.broker.get_portfolio_items()
        assert not portfolio

    def test4_buy_limit(self):
        """
        test buy if not enough money
        :return:
        """
        arguments_broker = {
            "portfolio_name": "limitstrategy",
            "portfolio_user": "user",
            "database_data": True,
            "expire_in_hours": 600,
            "db_tool": self.db_tool,
            "cash": 200000
        }
        broker_limit = DemoBroker(self.config, arguments_broker, self.test_logger)
        broker_limit.delete_portfolio(arguments_broker["portfolio_name"], "user")
        broker_limit.set_portfolio(arguments_broker["portfolio_name"], "user", 20000)
        with freeze_time("2017-10-09"):
            self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
            arguments_strategy = {
                "buy_percentage": 0.4,
                "sell_percentage": 1.,
                "buy_under_value_limit_percentage": -0.01,
                "commission_price_ratio_threshold_": .005,
                "order_type": OrderType.limit
            }

            strategy = Dsm(self.config, arguments_strategy, broker_limit, self.test_logger)

            strategy.start_strategy(buy=True, sell=False)
            strategy.start_strategy(buy=True, sell=False)
            strategy.start_strategy(buy=True, sell=False)
            broker_limit.commit_work()
            orders = broker_limit.db_tool.session.query(Orders)\
                .filter(Orders.order_type == OrderType.limit)\
                .filter(Orders.status == Status.confirmed).all()
            assert orders
            assert len(orders) >= 1
            assert orders[0].status.value == Status.confirmed.value

        with freeze_time("2017-10-15"):
            broker_limit.refresh()
            portfolio = broker_limit.get_portfolio_items()
            assert portfolio
            orders_com = self.db_tool.session.query(Orders).\
                filter(Orders.order_type == OrderType.limit).\
                filter(Orders.status == Status.completed).all()
            assert orders_com
            assert len(orders_com) >= 1
        broker_limit.delete_portfolio(broker_limit.get_portfolio_name(),
                                      broker_limit.get_portfolio_user())

    @freeze_time("2017-10-01 ")
    def test_5_test_piotroski(self):
        """
        Tests the piotroski strategy
        :return:
        """
        self.db_tool.session.query(Orders).delete()
        self.db_tool.session.query(Filter).delete()
        self.db_tool.session.query(Signal).filter(Signal.name == 'FakeSignal').delete()
        self.db_tool.commit()
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.create_fake_filter(PiotroskiScore.NAME, 8, 2, datetime.datetime.now(),
                                self.stock_list[0:1])
        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "threshold": 8,
            "filter_name": PiotroskiScore.NAME,
            "ignore_signals": ["FakeSignal"],
            "order_type": OrderType.market
        }
        strategy = Sf(self.config, arguments_strategy, self.broker, self.test_logger)
        strategy.start_strategy(sell=False, buy=True)
        self.broker.commit_work()
        orders = self.db_tool.session.query(Orders)\
            .filter(Orders.order_type == OrderType.market)\
            .filter(Orders.status == Status.completed).all()
        assert not orders
        arguments_strategy["ignore_signals"] = None
        strategy = Sf(self.config, arguments_strategy, self.broker, self.test_logger)
        strategy.start_strategy(sell=False, buy=True)
        self.broker.commit_work()
        orders = self.db_tool.session.query(Orders)\
            .filter(Orders.order_type == OrderType.market)\
            .filter(Orders.status == Status.completed).all()
        assert orders
        assert len(orders) == 1
        self.set_fake_signals(datetime.datetime.now())
        strategy.start_strategy(buy=False, sell=True)
        self.broker.refresh()
        portfolio = self.broker.get_portfolio_items()
        assert not portfolio

    @freeze_time("2017-10-01")
    def test_6_test_levermann(self):
        """
        Tests the levermann strategy
        :return:
        """
        self.db_tool.session.query(Orders).delete()
        self.db_tool.session.query(Signal).filter(Signal.name == 'FakeSignal').delete()
        self.db_tool.commit()
        self.create_fake_filter(LevermannScore.NAME, 10, 2, datetime.datetime.now(),
                                self.stock_list[0:1])
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list[0:1],
                                 'UltimateOscillatorCrossEmaSignal')
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list[0:1],
                                 'UltimateOscillatorCrossEmaSignal')
        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "threshold": 10,
            "filter_name": LevermannScore.NAME,
            "order_type": OrderType.market
        }
        strategy = Sf(self.config, arguments_strategy, self.broker, self.test_logger)
        strategy.start_strategy(sell=False, buy=True)
        self.broker.commit_work()
        self.db_tool.session.query(Orders).delete()
        strategy.start_strategy(buy=True, sell=False)
        self.broker.commit_work()
        my_orders = [self.db_tool.session.query(Orders).all()]
        assert len(my_orders) == 1
        orders = self.db_tool.session.query(Orders)\
            .filter(Orders.order_type == OrderType.market)\
            .filter(Orders.status == Status.completed).all()
        assert orders
        assert len(orders) == 1
        self.set_fake_signals(datetime.datetime.now())
        self.set_fake_signals(datetime.datetime.now(),
                              signal_name='UltimateOscillatorCrossEmaSignal')
        strategy.start_strategy(buy=False, sell=True)
        self.broker.refresh()
        portfolio = self.broker.get_portfolio_items()
        assert not portfolio

    @freeze_time("2017-10-01")
    def test_7_test_tool(self):
        """
        Tests the strategy execution tool
        :return:
        """
        arguments_broker = {
            "portfolio_name": "",
            "portfolio_user": "user",
            "database_data": False,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        arguments = {
            'strategies': "ALL",
            'mode': "demo",
            'strategy_name_prefix': 'UnitTest',
            'db_tool': self.db_tool,
            "broker": DemoBroker(self.config, arguments_broker, self.test_logger)
        }
        test = 0
        test += StartStrategy(self.config, arguments, self.test_logger).build()
        assert test == 0

    @freeze_time("2017-09-21 09:21:34")
    def test_8_back_testing(self):
        """
        test the back testing tool for strategies
        :return:
        """
        tz = TraderBase.get_timezone()
        logging.basicConfig(level=logging.DEBUG)
        date_now = datetime.datetime.now(tz=tz)
        date_fake_starts = date_now - datetime.timedelta(days=150)
        config = TraderBase.get_config()
        my_parameter = [Parameter(value=5), Parameter(value=6)]
        signal_list = self.create_fake_signals(-2, date_fake_starts, [1],
                                               'UltimateOscillatorCrossEmaSignal', my_parameter)
        assert signal_list
        assert len(signal_list) == 1
        my_plot = Plot()
        my_plot.add_plot_to_data({})
        signal_list[0].plot.append(
            my_plot
        )
        self.db_tool.commit()
        arguments_broker = {
            "portfolio_name": "",
            "portfolio_user": "user",
            "database_data": True,
            "db_tool": self.db_tool,
            "cash": 2000
        }
        arguments = {
            "strategies": ["SimpleMarket40"],
            "signals": ["Uoe"],
            "stocks": [1],
            "look_back": 400,
            "db_tool": self.db_tool,
            "broker":  DemoBroker(config, arguments_broker, self.test_logger),
            "from_date": date_fake_starts,
            "to_date": date_now
        }
        BackTestingStrategy(config, arguments, self.test_logger).build()
        arguments["broker"].commit_work()
        json_data = self.db_tool.session.query(Plot).\
            filter(Plot.signal_id == signal_list[0].id).first()
        assert json_data.data
        json_data = json_data.get_plot()
        assert json_data != '{}'
        # todo analyse more functions with default datetime.now() arguments
        # todo solve monday not tlrade issue
        tz = TraderBase.get_timezone()
        sell_date = [datetime.datetime.fromtimestamp(int(data["x"])/1000, tz=tz)
                     for data in json_data[1]["data"] if data["text"] == "Sell"]
        buy_date = [datetime.datetime.fromtimestamp(int(date["x"])/1000, tz=tz)
                    for date in json_data[1]["data"] if date["text"] == "Buy"]
        assert sell_date and buy_date
        # now we check if strategy really bought stocky by signal
        sell_date = [item for item in sell_date if date_now >= item >= date_fake_starts]
        buy_date = [item for item in buy_date if date_now >= item >= date_fake_starts]
        assert sell_date and buy_date
        # remove first sell signal if younger than first buy signal
        if sell_date[0] < buy_date[0]:
            sell_date.pop(0)

        my_orders_buy = [x[0] for x in self.db_tool.session.query(Orders.date).
                         filter(Orders.is_sell == 0).order_by(Orders.date).all()]
        my_orders_sell = [x[0] for x in self.db_tool.session.query(Orders.date).
                          filter(Orders.is_sell == 1).order_by(Orders.date).all()]
        assert len(my_orders_buy) == len(buy_date)
        assert len(my_orders_sell) == len(sell_date)

        def check_date(date_list1, date_list2):
            """
            returns false if date in list is unequal
            :param date_list1:
            :param date_list2:
            :return:
            """
            for idx, my_date1 in enumerate(date_list1):
                if my_date1.replace(tzinfo=tz).date() != date_list2[idx].date():
                    return False
            return True
        assert check_date(my_orders_buy, buy_date), \
            " The given date lists are not equal %s %s" % (my_orders_buy, buy_date)
        assert check_date(my_orders_sell, sell_date), \
            " The given date lists are not equal %s %s" % (my_orders_sell, sell_date)

    @freeze_time("2017-10-01")
    def test_9_group_strategy(self):
        """
        Tests the group strategy
        :return:
        """
        self.delete_all_fake_signals()

        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "group_size": 5,
            "order_type": OrderType.market
        }
        strategy = Sg(self.config, arguments_strategy, self.broker, self.test_logger)

        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, 'FakeSignal1')
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, 'FakeSignal2')
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, 'FakeSignal3')
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, 'FakeSignal4')

        strategy.start_strategy(sell=False, buy=True)
        self.broker.commit_work()
        orders = self.db_tool.session.query(Orders)\
            .filter(Orders.order_type == OrderType.market)\
            .filter(Orders.status == Status.completed).all()
        assert not orders

        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, 'FakeSignal5')

        strategy.start_strategy(sell=False, buy=True)
        orders = self.db_tool.session.query(Orders)\
            .filter(Orders.order_type == OrderType.market)\
            .filter(Orders.status == Status.completed).all()

        assert orders

    @freeze_time("2017-10-01 09:00:00")
    def test_10_test_filter_signal_strategy(self):
        # check on_run_counter method
        assert Sfs.on_run_counter([], []) == 0
        assert Sfs.on_run_counter(None, [1]) == 0
        assert Sfs.on_run_counter([1], None) == 0
        assert Sfs.on_run_counter(None, None) == 0

        assert Sfs.on_run_counter([{'price': 3}, {'price': 4}, {'price': 5}, {'price': 6}],
                                  [{'price': 2}, {'price': 2}, {'price': 2}, {'price': 2}]) == 4

        assert Sfs.on_run_counter([{'price': 4}, {'price': 5}, {'price': 6}],
                                  [{'price': 2}, {'price': 2}, {'price': 2}, {'price': 2}]) == 3

        assert Sfs.on_run_counter([{'price': 4}, {'price': 5}, {'price': 6}],
                                  [{'price': 2}, {'price': 2}]) == 2

        assert Sfs.on_run_counter([{'price': 4}, {'price': 5}, {'price': 6}],
                                  [{'price': 2}, {'price': 44}, {'price': 33}]) == 1
        # check if find price works
        date_fake_starts = datetime.datetime.now() - datetime.timedelta(days=150)
        my_plot = self.__get_plot_data(1, date_fake_starts, datetime.datetime.now())
        assert my_plot
        assert not Sfs.find_price_helper(None, [])
        assert not Sfs.find_price_helper(1, [])
        assert Sfs.find_price_helper(1496095200000, my_plot.get_plot()[0]) == 172.0, \
            "1496095200000 doesnt contains in plot %s" % my_plot.data[0]
        # check if parse plot works
        buy_data, sell_data = Sfs.parse_plot_data([my_plot])
        assert buy_data and sell_data and len(sell_data) == len(buy_data)
        my_plot_data = my_plot.get_plot()
        my_plot_data[1]["data"].append({'text': 'Sell', 'x': 1396095200000})
        my_plot.add_plot_to_data(my_plot_data)
        buy_data, sell_data = Sfs.parse_plot_data([my_plot])
        buy_data, sell_data = Sfs.parse_plot_data([my_plot])
        assert buy_data and sell_data and len(sell_data) == len(buy_data)
        my_plot_data = my_plot.get_plot()
        my_plot_data[1]["data"].append({'text': 'Buy', 'x': 1896095200000})
        my_plot.add_plot_to_data(my_plot_data)
        buy_data, sell_data = Sfs.parse_plot_data([my_plot])
        assert buy_data and sell_data and len(sell_data) == len(buy_data)
        # check if data is in correct order
        for idx in range(len(buy_data)):
            assert sell_data[idx]['time'] > buy_data[idx]['time']
        # check teh whole strategy
        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "threshold": 2,
            "mode": Sfs.ONLY_BUY_WHEN_ON_RUN,
            "order_type": OrderType.market
        }

        strategy = Sfs(self.config, arguments_strategy, self.broker, self.test_logger)
        self.create_fake_signals(2, datetime.datetime.now(), [1],
                                 'FakeSignal1', plot_data=my_plot)
        my_signals = strategy.get_relevant_buy_signals()
        assert not my_signals

        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "threshold": 1,
            "mode": Sfs.ONLY_BUY_WHEN_ON_RUN,
            "order_type": OrderType.market
        }
        strategy = Sfs(self.config, arguments_strategy, self.broker, self.test_logger)
        my_signals = strategy.get_relevant_buy_signals()
        assert my_signals

    @freeze_time("2017-10-01")
    def test_11_test_one_signal(self):
        """
        Tests the one signal strategy strategy
        :return:
        """
        self.db_tool.session.query(Orders).delete()
        self.db_tool.session.query(Signal).filter(Signal.name == 'FakeSignal').delete()
        self.db_tool.commit()
        self.create_fake_filter(LevermannScore.NAME, 10, 2, datetime.datetime.now(),
                                self.stock_list[0:1])
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list[0:1],
                                 'UltimateOscillatorCrossEmaSignal')
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list[0:1],
                                 'UltimateOscillatorCrossEmaSignal')
        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "threshold": 10,
            "filter_name": LevermannScore.NAME,
            "order_type": OrderType.market,
            "signal_name": "UltimateOscillatorCrossEmaSignal"
        }
        strategy = Sos(self.config, arguments_strategy, self.broker, self.test_logger)
        strategy.start_strategy(sell=False, buy=True)
        self.broker.commit_work()
        self.db_tool.session.query(Orders).delete()
        strategy.start_strategy(buy=True, sell=False)
        self.broker.commit_work()
        my_orders = [self.db_tool.session.query(Orders).all()]
        assert len(my_orders) == 1
        orders = self.db_tool.session.query(Orders) \
            .filter(Orders.order_type == OrderType.market) \
            .filter(Orders.status == Status.completed).all()
        assert orders
        assert len(orders) == 1
        self.set_fake_signals(datetime.datetime.now())
        self.set_fake_signals(datetime.datetime.now(),
                              signal_name='UltimateOscillatorCrossEmaSignal')
        strategy.start_strategy(buy=False, sell=True)
        self.broker.refresh()
        portfolio = self.broker.get_portfolio_items()
        assert not portfolio

    @freeze_time("2017-10-01")
    def test_12_only_take_signal_with_max_profit(self):
        """
        Checks if strategy buy.
        """
        my_profit_list_1 = [-0.2, 0.9, 3.2, 0.2, 0.5, 1.2, -2.0, 4.0, 3.2, -1.2]
        my_profit_list_2 = [-1.2, 3.9, 2.2, 11.2, 3.5, 1.2, -4.0, 4.4, 2.2, -33.2]
        my_profit_list_3 = [-3.2, 0.9, 3.2, 0.2, 0.5, 1.2, -2.0, 4.2, 3.2, -1.2]
        my_profit_list_4 = [-0.2, 0.9, 3.2, 55.0, 0.5, 4.2, -2.0, 4.0, 3.2, -1.2]
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Ema",
                                 profit_list=my_profit_list_1)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Uma",
                                 profit_list=my_profit_list_2)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Dma",
                                 profit_list=my_profit_list_3)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Cma",
                                 profit_list=my_profit_list_4)
        my_profit_list = [-0.2, 0.9, 3.2, 0.2, 0.5, 1.2, -2.0, 4.0, 3.2, -1.2]
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list,
                                 profit_list=my_profit_list)
        self.db_tool.commit()
        self.strategy.start_strategy(buy=True, sell=False)
        self.broker.refresh()
        portfolio = self.broker.get_portfolio_items()
        assert portfolio
        assert len(portfolio) == len(self.stock_list)
        signal_ids = self.db_tool.session.query(Signal.id). \
            filter(Signal.profit_in_percent == 55.0).all()
        signal_ids = [my_id[0] for my_id in signal_ids]
        for item in portfolio:
            assert item['stock_id'] in self.stock_list
            assert item["signal_id"] in signal_ids

    @freeze_time("2017-10-01")
    def test_13_only_take_signal_with_max_profit_filter(self):
        """
        Checks if strategy buy.
        """
        my_profit_list_1 = [-0.2, 0.9, 3.2, 0.2, 0.5, 1.2, -2.0, 4.0, 3.2, -1.2]
        my_profit_list_2 = [-1.2, 3.9, 2.2, 11.2, 3.5, 1.2, -4.0, 4.4, 2.2, -33.2]
        my_profit_list_3 = [-3.2, 0.9, 3.2, 0.2, 0.5, 1.2, -2.0, 4.2, 3.2, -1.2]
        my_profit_list_4 = [-0.2, 0.9, 3.2, 55.0, 0.5, 4.2, -2.0, 4.0, 3.2, -1.2]
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Ema",
                                 profit_list=my_profit_list_1)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Uma",
                                 profit_list=my_profit_list_2)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Dma",
                                 profit_list=my_profit_list_3)
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="Cma",
                                 profit_list=my_profit_list_4)
        self.create_fake_filter(PiotroskiScore.NAME, 8, 2, datetime.datetime.now(),
                                self.stock_list)
        self.db_tool.commit()
        arguments_strategy = {
            "buy_percentage": 0.4,
            "sell_percentage": 1.,
            "commission_price_ratio_threshold_": 1.,
            "threshold": 8,
            "filter_name": PiotroskiScore.NAME,
            "order_type": OrderType.market
        }
        strategy = Sf(self.config, arguments_strategy, self.broker, self.test_logger)
        strategy.start_strategy(sell=False, buy=True)
        self.broker.commit_work()
        portfolio = self.broker.get_portfolio_items()
        assert portfolio
        assert len(portfolio) == len(self.stock_list)
        signal_ids = self.db_tool.session.query(Signal). \
            filter(Signal.profit_in_percent == 55.0).all()
        signal_ids = [my_id.id for my_id in signal_ids]
        for item in portfolio:
            assert item['stock_id'] in self.stock_list
            assert item["signal_id"] in signal_ids

    @freeze_time("2017-10-02")
    def test14_double_buy(self):
        """
        Checks if no double buy occurs.
        """
        self.create_fake_signals(2, datetime.datetime.now(), self.stock_list)
        self.db_tool.commit()
        self.strategy.start_strategy(buy=True, sell=False)
        self.broker.refresh()
        portfolio1 = self.broker.get_portfolio_items()
        self.strategy.start_strategy(buy=True, sell=False)
        self.broker.refresh()
        portfolio2 = self.broker.get_portfolio_items()
        self.strategy.start_strategy(buy=True, sell=False)
        self.broker.commit_work()
        with freeze_time("2017-10-19"):
            self.create_fake_signals(2, datetime.datetime.now(), self.stock_list, signal_name="ema",
                                     profit_list=[20, 30, 56])
            self.strategy.start_strategy(buy=True, sell=False)
        portfolio3 = self.broker.get_portfolio_items()
        assert len(portfolio1) == len(portfolio2) == len(portfolio3)
        for idx, item in enumerate(portfolio1):
            assert item["size"] == portfolio2[idx]["size"] == portfolio3[idx]["size"]
            assert item['stock_id'] == portfolio2[idx]['stock_id'] == portfolio3[idx]['stock_id']

    def __get_plot_data(self, stock_id, start_date, end_date):
        stock = self.db_tool.session.query(Stock).filter(Stock.id == stock_id).first()
        if stock:
            params = [2, 7]
            arguments = {
                'symbol': stock.symbol,
                'bars': None,
                'parameters': params,
                'optimizable': False,
                'name': MovingAverageCrossSignal.NAME,
                'plot_result': False
            }

            strategy = MovingAverageCrossSignal(
                arguments,
                self.test_logger
            )

            strategy.set_bars(
                stock.get_bars(
                    start=start_date,
                    end=end_date,
                    output_type=BARS_NUMPY
                )
            )

            strategy.generate_signals()
            return Plot(
                data=strategy.get_plot()
            )

    def create_fake_filter(self, name, value, status, date_now, stock_list):
        """

        :param name:
        :param value:
        :param status:
        :param date_now:
        :param stock_list:
        :return:
        """
        stocks = self.db_tool.session.query(Stock).filter(Stock.id.in_(stock_list)).all()

        for stock in stocks:
            stock.filter.append(
                Filter(
                    name=name,
                    status=status,
                    value=value,
                    date=date_now
                )
            )

        self.db_tool.commit()

    def create_fake_signals(self, status, date_now, stock_list, signal_name='FakeSignal',
                            parameter_list=None, plot_data=None, profit_list=None):
        """
        Create a fake signal with the name FakeSignal
        :param status:
        :param date_now:
        :param stock_list:
        :param signal_name:
        :param parameter_list:
        :param plot_data:
        :param profit_list
        :return:
        """
        if profit_list is None:
            profit_list = [1.0]
        my_signal_list = []
        stocks = self.db_tool.session.query(Stock)\
            .filter(Stock.id.in_(stock_list))

        for stock in stocks:
            for profit in profit_list:
                my_signal = Signal(
                    profit_in_percent=profit,
                    name=signal_name,
                    status=status,
                    date=date_now,
                    refresh_date=date_now
                )
                if plot_data:
                    my_signal.plot.append(plot_data)
                if parameter_list:
                    for parameter in parameter_list:
                        my_signal.parameter.append(parameter)
                stock.signal.append(my_signal)
                my_signal_list.append(my_signal)
        self.db_tool.commit()
        return my_signal_list

    def set_fake_signals(self, date_now, status=-2, signal_name='FakeSignal'):
        """
        Set all fake signals to sell status
        :param date_now:
        :param status:
        :param signal_name:
        :return:
        """
        signals = self.db_tool.session.query(Signal).filter(Signal.name == signal_name).all()
        # we have to refresh fake signals
        for signal in signals:
            signal.refresh_date = date_now
            signal.status = status

        self.db_tool.commit()

    def delete_all_fake_signals(self):
        """
        Delete all signals
        :return:
        """
        self.db_tool.session.query(Orders).filter(Orders.orders_id >= 0).delete()
        self.db_tool.session.query(Orders).delete()
        self.db_tool.session.query(Parameter).delete()
        self.db_tool.session.query(Plot).delete()
        self.db_tool.session.query(Signal).delete()
        self.db_tool.commit()

    def delete_all(self):
        self.broker.delete_portfolio(self.broker.get_portfolio_name(),
                                     self.broker.get_portfolio_user())
        self.delete_all_fake_signals()
        self.db_tool.session.query(Orders).filter(Orders.orders_id >= 0).delete()
        self.db_tool.session.query(Orders).delete()
        self.db_tool.session.query(Plot).delete()
        self.db_tool.session.query(Portfolio).delete()
        self.db_tool.commit()


if __name__ == '__main__':
    unittest.main()
