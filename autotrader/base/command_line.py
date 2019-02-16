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
import argparse
import datetime
import os
import sys
import yaml

from more_itertools import divide

from autotrader.broker.degiro.degiro_client import DegiroClient
from autotrader.broker.demo_broker import DemoBroker
from autotrader.datasource.database.app_database import StockDataBaseApp
from autotrader.datasource.database.app_schema import TagApp, StockApp, IndexApp, FilterApp, SeriesApp
from autotrader.datasource.database.stock_database import StockDataBase

from autotrader.base.trader_base import TraderBase
from autotrader.base.version import VERSION
from autotrader.datasource.database.stock_schema import Stock, Signal, Region, Tag, Index, Filter, Series
from autotrader.tool.database.create_and_fill_database import CreateAndFillDataBase
from autotrader.tool.database.update_database_stocks import UpdateDataBaseStocks
from autotrader.tool.filter.build_filters import BuildFilters
from autotrader.tool.filter.recreate_filters import RecreateFilters
from autotrader.tool.indicators.build_indicators_full import BuildIndicators
from autotrader.tool.indicators.build_indicators_quick import BuildIndicatorsQuick
from autotrader.tool.strategy.back_testing import BackTestingStrategy
from autotrader.tool.strategy.start_strategy import StartStrategy


def is_valid_file(parser, arg):
    """
    Check if file exists
    :param parser: parser instance
    :param arg: path to file
    :return: return the path if exists otherwise None
    """
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
        return None
    return arg


def get_arg_parse(args):
    """
    Parse arguments
    :return: None if args none otherwise ArgumentParser object
    """
    parser = argparse.ArgumentParser(description=
                                     'Commandline for the AutoTraderLib v {}'.format(VERSION))
    parser.add_argument('-i', '--install', dest='install', nargs='*',
                        help='Install database and fill with stocks. Attention: This option '
                             'will wipe all existing data.')
    parser.add_argument('-u', '--update', nargs='*', dest='update',
                        help='Update all series data of existing if you use "-u ALL" or '
                             'specific stocks if you use "-u HDD ADD RIB stocks')
    parser.add_argument('-U', '--update_sheets', nargs='*', dest='updatesheets',
                        help='Update all sheets data of existing if you use -U ALL" or specific'
                             ' stocks if  you use "-U HDD ADD RIB')
    parser.add_argument('-b', '--backup', dest='backup', nargs='*', action='store',
                        help='Backup database.')
    parser.add_argument('-f', '--build_filter', dest='filter', action='store', nargs='*',
                        help='Build filter indicators for all stocks')
    parser.add_argument('-r', '--rebuild_filter', dest='rebuild_filter', action='store', nargs='*',
                        help='Rebuild filter for all stocks')
    parser.add_argument('-d', '--delete_filter', dest='delete_filter', action='store', nargs='*',
                        help='Delete filter for all stocks')
    parser.add_argument('-dds', '--delete_demo_strategy', dest='delete_demo_strategy',
                        action='store', nargs='*',
                        help='Delete all demo test strategy data.')
    parser.add_argument('-dbs', '--delete_backtest_strategy', dest='delete_backtest_strategy',
                        action='store', nargs='*',
                        help='Delete all back test strategy data.')
    parser.add_argument('-s', '--build_signals', dest='signals', action='store', nargs='*',
                        help='Build statistical indicators for all stocks')
    parser.add_argument('-S', '--build_strategy', dest='strategy', action='store', nargs='*',
                        help='Execute strategy or all with ALL keyword.')
    parser.add_argument('-a', '--back_test_strategy', dest='back_test_strategy', nargs='*',
                        action='store', help='Tests all strategies from first signal to last.')
    parser.add_argument('-q', '--quick_build_signals', dest='quicksignals', action='store',
                        nargs='*', help='Quick build statistical indicators. Add ALL for all stocks'
                                        ' or a list of stock symbols for specific.')
    parser.add_argument("-c", "--config", dest="config", action='store',
                        help="path to the autotrader config file",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-l", "--live", dest="live", action='store_true',
                        help="Starts live trading.")
    parser.add_argument("-v", "--version", dest="version", action='store_true',
                        help="Returns the version of autotrader.")
    parser.add_argument('-t', '--task', dest='task', action='store', nargs='*',
                        help='Add task splitting', default=None)
    parser.add_argument('--dump', dest='dump', action='store_true',
                        help='Create yaml dump file', default=False)
    parser.add_argument('--appdb', dest='app', action='store_true',
                        help='Create app db file', default=False)
    if args is None or not args:
        parser.print_help()
        return None
    return parser.parse_args(args)


def get_stocks(db_tool, stocks_arg):
    """
    For multi processing purposes we have to split the task in small pieces.
    The BuildIndicator and BuildIndicatorQuick task is scalable by stock amount so we split stocks.
    :param db_tool:
    :param stocks_arg: when first item and second item are digits then we split all stocks
     in almost equal pieces otherwise the origin argument will returned. The first digit is the
     task id and the second the amount or tasks i.e 1 8 means we split all stocks in 8 pieces and
     return part 1.
    :return: when first item and second item are digits  a list of stock symbols otherwise
    the stocks_arg
    """
    if stocks_arg and len(stocks_arg) == 2 and \
            (type(stocks_arg[0]) == int or
             (type(stocks_arg[0]) == str and stocks_arg[0].isdigit())) and \
            (type(stocks_arg[1]) == int or
             (type(stocks_arg[1]) == str and stocks_arg[1].isdigit())):
        my_stocks = db_tool.session.query(Stock.id).all()
        my_stocks = [my_stock[0] for my_stock in my_stocks if my_stock]
        my_list = list([x for x in divide(int(stocks_arg[1]), my_stocks)][int(stocks_arg[0])])
        return my_list
    return ['ALL']


def get_from_to_dates(db_tool, date_arg):
    """
    The BackTesting Tool for strategies is scalable only by date. We build all dates from
    from_date until to_date [01.01.2019, 01.02.2019 ... 09.09.2023] and split the date list in small
    pieces for multi processing purposes.
    :param db_tool:
    :param date_arg: when first item and second item are digits then we split all dates
     in almost equal pieces otherwise the origin argument will returned. The first digit is the
     task id and the second the amount or tasks i.e 8 18 means we split all dates in 18 pieces and
     return part 8.
    :return:
    """
    from_date = None if db_tool is None else \
        db_tool.session.query(Signal.date).order_by(Signal.date).first()
    to_date = None
    if from_date is not None:
        from_date = from_date[0]
        to_date = datetime.datetime.now()
    if date_arg and len(date_arg) == 2 and \
            (type(date_arg[0]) == int or (type(date_arg[0]) == str and date_arg[0].isdigit())) and \
            (type(date_arg[1]) == int or (type(date_arg[1]) == str and date_arg[1].isdigit())):
        my_dates = [my_date for my_date in BackTestingStrategy.date_range(from_date, to_date)]
        my_list = list([x for x in divide(int(date_arg[1]), my_dates)][int(date_arg[0])])
        if len(my_list) > 1:
            return [my_list[0], my_list[-1]]
    return [from_date, to_date]


def build_app_db(logger, db_tool):
    db_tool_app = StockDataBaseApp(logger)
    db_tool_app.connect()
    db_tool_app.create()
    my_indices = db_tool.session.query(Index).all()
    for my_index in my_indices:
        my_index_app = IndexApp(
            symbol=my_index.symbol
        )
        for my_stock in my_index.stocks:
            stock_item = db_tool_app.session.query(StockApp).filter(StockApp.name == my_stock.name). \
                first()
            if stock_item is None:
                stock_item = StockApp(
                    symbol=my_stock.symbol,
                    name=my_stock.name,
                    category=my_stock.category,
                )
                for my_tag in my_stock.tags:
                    my_tag_app = db_tool_app.session.query(TagApp).filter(TagApp.tag == my_tag.tag). \
                        filter(TagApp.category == 'industry').first()
                    if my_tag_app is None:
                        my_tag_app = TagApp(
                            tag=my_tag.tag,
                            category='industry'
                        )
                        db_tool_app.session.add(my_tag_app)
                    my_tag_app.stocks.append(stock_item)

                region = my_stock.region
                if region is None:
                    region = 'unknown'
                else:
                    region = region.region
                tag_in_db_region = db_tool_app.session.query(TagApp).filter(TagApp.tag == region). \
                    filter(TagApp.category == 'region').first()
                if tag_in_db_region is None:
                    tag_in_db_region = TagApp(
                        tag=region,
                        category='region'
                    )
                    db_tool_app.session.add(tag_in_db_region)
                tag_in_db_region.stocks.append(stock_item)

                my_filters = db_tool.session.query(Filter).filter(Filter.stock_id == my_stock.id).\
                    order_by(Filter.date.desc()).limit(100)

                my_series = db_tool.session.query(Series).filter(Series.stock_id == my_stock.id).\
                    order_by(Series.date.desc()).limit(100)
                currency = '€'
                if my_index.symbol in ['DOW JONES', 'NASDAQ 100', 'S&P 100', 'S&P 500']:
                    currency = '$'
                elif my_index.symbol in ['FTSE 100']:
                    currency = '£'
                for my_data in my_series:
                    stock_item.series.append(
                        SeriesApp(
                            priceopen=my_data.priceopen,
                            priceclose=my_data.priceclose,
                            pricehigh=my_data.pricehigh,
                            pricelow=my_data.pricelow,
                            volume=my_data.volume,
                            currency=currency,
                            date=my_data.date,
                        )
                    )
                for my_filter in my_filters:
                    stock_item.filter.append(
                        FilterApp(
                            value=my_filter.value,
                            name=my_filter.name,
                            status=my_filter.status,
                            date=my_filter.date,
                        )
                    )
            my_index_app.stocks.append(stock_item)
        db_tool_app.session.add(my_index_app)
    db_tool_app.session.commit()
    db_tool.close()


def build_yaml_file(db_tool):
    my_stocks = db_tool.session.query(Stock).all()
    my_stocks_list = {'stocks': []}
    for stock in my_stocks:
        stock_item = {
            'id': stock.id,
            'name': stock.name,
            'symbol': stock.symbol,
            'country': stock.region.region if stock.region else 'unknown',
            'indices': [index.symbol for index in stock.indices],
            'industries': list(set([tag.tag for tag in stock.tags])),
            'exchanges': {
                'FRA': {
                    'yahoo_symbol': '{}.F'.format(stock.symbol),
                    'google_symbol': 'FRA:{}'.format(stock.symbol)
                },
                'OTC': {
                    'yahoo_symbol': '{}'.format(stock.symbol),
                    'google_symbol': 'NASDAQ:{}'.format(stock.symbol)
                },
            }
        }
        my_stocks_list['stocks'].append(stock_item)
    with open("output_file.yml", "w") as output_stream:
        yaml.dump(my_stocks_list, output_stream, default_flow_style=False, sort_keys=False)


def autotrader_app():
    """
    Main entry point for autotrader application
    :return:
    """
    # print usage when no option is given
    parsed_args = get_arg_parse(sys.argv[1:])
    exit_code = 0

    if not parsed_args:
        return False

    if parsed_args.config:
        config = TraderBase.get_config(parsed_args.config)
        logger = TraderBase.setup_logger("autotrader")
        db_tool = StockDataBase(config["sql"], logger)
        db_tool.connect()

        print("Autotrader {}".format(VERSION))
        if parsed_args.app:
            build_app_db(logger, db_tool)
        if parsed_args.dump:
            build_yaml_file(db_tool)
        if parsed_args.install is not None:
            datasource = DegiroClient(config['degiro'], {"db_tool": None}, logger)
            arguments = {
                'stocks_to_update': ['ALL'],  # For UpdateDataBaseStocks
                'update_stocks': False,       # For UpdateDataBaseStocks
                'update_sheets': True,        # For UpdateDataBaseStocks
                'db_tool': db_tool,
                'datasource': datasource
            }
            exit_code += CreateAndFillDataBase(config, arguments, logger).build()
            exit_code += UpdateDataBaseStocks(config, arguments, logger).build()
        if parsed_args.update is not None:
            arguments = {
                'stocks_to_update': parsed_args.update,
                'update_stocks': True,
                'update_sheets': False,
                'db_tool': db_tool,
                'datasource': DegiroClient(config['degiro'], {"db_tool": db_tool}, logger)
            }
            exit_code += UpdateDataBaseStocks(config, arguments, logger).build()
        if parsed_args.updatesheets is not None:
            arguments = {
                'stocks_to_update': parsed_args.updatesheets,
                'update_stocks': False,
                'update_sheets': True,
                'db_tool': db_tool,
                'datasource': DegiroClient(config['degiro'], {"db_tool": db_tool}, logger)
            }
            exit_code += UpdateDataBaseStocks(config, arguments, logger).build()
        if parsed_args.backup is not None:
            raise NotImplementedError
        if parsed_args.filter is not None:
            arguments = {
                'db_tool': db_tool
            }
            exit_code += BuildFilters(arguments, logger).build()
        if parsed_args.rebuild_filter is not None:
            from_date, to_date = get_from_to_dates(db_tool, parsed_args.task)
            arguments = {
                'db_tool': db_tool,
                "from_date": from_date,
                "to_date": to_date,
                'filters': parsed_args.rebuild_filter
            }
            exit_code += RecreateFilters(arguments, logger).build()
        if parsed_args.delete_filter is not None:
            arguments = {
                'db_tool': db_tool,
                'filters': parsed_args.delete_filter
            }
            my_recreate = RecreateFilters(arguments, logger)
            my_recreate.delete_old_filter()
        if parsed_args.delete_backtest_strategy is not None:
            arguments_broker = {
                "portfolio_name": "",
                "portfolio_user": "user",
                "database_data": True,
                "db_tool": db_tool,
                "cash": 2000
            }
            arguments = {
                'strategies': ["ALL"],
                'broker': DemoBroker(config, arguments_broker, logger),
                'strategy_name_prefix': 'B',
                'db_tool': db_tool
            }
            StartStrategy(config, arguments, logger).recreate_all_strategies()
            arguments["broker"].commit_work()
        if parsed_args.delete_demo_strategy is not None:
            arguments_broker = {
                "portfolio_name": "",
                "portfolio_user": "user",
                "database_data": True,
                "db_tool": db_tool,
                "cash": 2000
            }
            arguments = {
                'strategies': ["ALL"],
                'broker': DemoBroker(config, arguments_broker, logger),
                'strategy_name_prefix': 'D',
                'db_tool': db_tool
            }
            StartStrategy(config, arguments, logger).recreate_all_strategies()
            arguments["broker"].commit_work()
        if parsed_args.signals is not None:
            # split all stocks in almost equal pieces and get part of split by task id
            my_stocks = get_stocks(db_tool, parsed_args.task)
            arguments = {
                'signals': ["ALL"],
                'stocks': my_stocks,
                "look_back": 300,
                'db_tool': db_tool
            }
            exit_code += BuildIndicators(config, arguments, logger).build()
        if parsed_args.quicksignals is not None:
            # split all stocks in almost equal pieces and get part of split by task id
            my_stocks = get_stocks(db_tool, parsed_args.task)
            arguments = {
                'signals': ["ALL"],
                'stocks': my_stocks,
                "look_back": 300,
                'db_tool': db_tool
            }
            exit_code += BuildIndicatorsQuick(config, arguments, logger).build()
        if parsed_args.live:
            arguments_broker = {
                "portfolio_name": "degiro",
                "portfolio_user": "user",
                "database_data": False,
                "db_tool": db_tool
            }
            degiro = DegiroClient(config["degiro"], arguments_broker, logger)
            degiro.login()
            arguments = {
                'strategies': ["SecureHotH6MonthT50V40"],
                'broker': degiro,
                'strategy_name_prefix': 'L',
                'db_tool': db_tool
            }
            exit_code += StartStrategy(config, arguments, logger).build()
        if parsed_args.strategy is not None:
            arguments_broker = {
                "portfolio_name": "",
                "portfolio_user": "user",
                "database_data": False,
                "db_tool": db_tool,
                "cash": 2000
            }
            arguments = {
                'strategies': parsed_args.strategy,
                'broker': DemoBroker(config, arguments_broker, logger),
                'strategy_name_prefix': 'D',
                'db_tool': db_tool
            }
            exit_code += StartStrategy(config, arguments, logger).build()
            arguments["broker"].commit_work()
        if parsed_args.back_test_strategy is not None:
            arguments_broker = {
                "portfolio_name": "",
                "portfolio_user": "user",
                "database_data": True,
                "db_tool": db_tool,
                "cash": 2000
            }
            backtest_days = int(config['autotrader']['backtest_days'])
            from_date, to_date = datetime.datetime.now() + datetime.timedelta(days=-backtest_days), \
                datetime.datetime.now()
            arguments = {
                "strategies": ["ALL"],
                'stocks': ["ALL"],
                "signals": ["ALL"],
                'db_tool': db_tool,
                "broker":  DemoBroker(config, arguments_broker, logger),
                "from_date": from_date,
                "to_date": to_date
            }
            exit_code += BackTestingStrategy(config, arguments, logger).build()
            arguments["broker"].commit_work()
    if parsed_args.version:
        print(VERSION)
    return exit_code
