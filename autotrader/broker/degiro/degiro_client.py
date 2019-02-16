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
import enum
import json
import logging
from datetime import datetime, timedelta, date
from time import sleep

from dateutil import parser
from dateutil.relativedelta import relativedelta

from autotrader.base.dict_helper import DictHelper
from autotrader.base.network_tool import NetworkTool
from autotrader.base.trader_base import TraderBase
from autotrader.broker.broker_base import BrokerBase
from autotrader.broker.degiro.degiro_config_helper import DegiroConfigHelper as Ch
from autotrader.broker.degiro.degiro_data_helper import DegiroDataHelper
from autotrader.datasource.database.stock_schema import Portfolio, Orders, Status, OrderType, Stock


class DegiroClient(BrokerBase):
    """
    Degiro client implementation
    """
    class DegiroTimeType(enum.Enum):
        intraDay = 1
        unlimited = 3

    class DegiroOrderType(enum.Enum):
        """
        Enum for order types

        market buy: buySell	BUY orderType 2 productId 3934 size 2 timeType 3
        market sell: buySelL SELL orderType 2 productId 3934 size 2 timeType 3

        limit buy: buySell BUY orderType 0 price 45 productId 3934 size 2 timeType
        limit sell: buySell SELL orderType 0 price 45 productId 3934 size 2 timeType
        """
        limit = 0
        market = 2
        stoploss = 3
        stoplimit = 1
        trailingstop = 13

    def get_portfolio_object(self):
        if self.db_tool is None:
            return None
        portfolio = self.db_tool.session.query(Portfolio) \
            .filter(self.portfolio_name == Portfolio.name)\
            .filter(self.portfolio_user == Portfolio.user).first()
        return portfolio

    def exist_portfolio(self, name, user):
        """
        Checks if the portfolio exists
        :param name: the name of portfolio
        :param user: the portfolio owner
        :return: true if exists otherwise false
        """
        if self.db_tool is None:
            return None
        portfolio = self.db_tool.session.query(Portfolio) \
            .filter(self.portfolio_user == Portfolio.user)\
            .filter(name == Portfolio.name).first()
        return portfolio is not None

    def get_cash(self):
        """
        :return:
        """
        params = {
            "cashFunds": 0,
        }
        my_url = "{}v5/update/{};jsessionid={}".format(self.degiro_api_urls["tradingUrl"],
                                                       self.init_account, self.session_id)
        response = self.network_tool.get(my_url, params)

        if response:
            data = response.json()
            try:
                cash_items = data['cashFunds']['value']
                for cash_item in cash_items:
                    for value in cash_item['value']:
                        if value['name'] == 'value' and type(value['value']) == float:
                            return value['value']
            except (ValueError, KeyError):
                self.logger.exception("Could not completed parse cash of portfolio.")
        return None

    def get_status(self, order_id):
        data = self.get_order_history_all()
        try:
            for item in data:
                if order_id == item['orderId']:
                    return item["status"]
        except KeyError:
            self.logger.exception("Couldnt parse the status of orderid {}".format(order_id))
        return None

    def refresh(self, from_date=datetime.now() - timedelta(days=60), to_date=datetime.now()):
        portfolio = self.get_portfolio_object()
        orders = self.db_tool.session.query(Orders).filter(Orders.portfolio_id == portfolio.id).\
            filter(Orders.status != 'completed').all()
        # we have to parse transaction
        my_transactions = self.get_transaction_history(from_date, to_date)
        if my_transactions is None:
            raise RuntimeError("Could not collect transactions")
        for order in orders:
            product_id = self.get_order_id_of_stock(order.stock.symbol, order.stock.exchange.symbol)
            if product_id is None:
                raise RuntimeError("Could not collect product id for {}".format(order.stock.symbol))
            for transaction in my_transactions:
                if transaction['productId'] == int(product_id) and \
                        ((transaction['buysell'] == 'B' and not order.is_sell) or
                         (transaction['buysell'] == 'S' and order.is_sell)) and \
                        transaction["quantity"] == order.size and \
                        order.date.date() == parser.parse(transaction["date"]).date():
                    order.price = transaction["price"]
                    order.commission = abs(transaction["feeInBaseCurrency"])
                    order.price_complete = transaction["totalPlusFeeInBaseCurrency"]
                    order.status = Status.completed
                    if order.is_sell:
                        self.connect_related_order(order)
            if order.status.value == Status.confirmed.value:
                now = datetime.now()
                expire_date = order.expire_date
                if now > expire_date:
                    order.status = Status.expired
        self.db_tool.commit()

    def __init__(self, degiro_config, arguments, logger: logging.Logger):
        super(DegiroClient, self).__init__("degiro", arguments, logger)
        self.username = degiro_config['user']
        self.password = degiro_config['pw']
        self.portfolio_name = "degiro"
        self.portfolio_user = degiro_config['user']
        self.session_id = None
        self.degiro_id = None
        self.init_account = None
        self.network_tool = NetworkTool(logger)
        self.degiro_config = None
        self.db_tool = arguments.get('db_tool', None)
        if self.db_tool and not self.exist_portfolio(self.portfolio_name, self.portfolio_user) \
                and self.db_tool.is_connected():
            portfolio = Portfolio(
                name=self.portfolio_name,
                user=self.portfolio_user,
                cash=0,
                initial_cash=0
            )
            self.db_tool.session.add(portfolio)
            self.db_tool.commit()
        self.degiro_api_urls = {}
        base = 'https://trader.degiro.nl/'
        self.api_urls = {
            "LOGIN_URL": base + 'login/secure/login',
            "CONFIG_URL": base + 'pa/secure/client',
            "PRODUCT_URL": base + 'product_search/secure/v5/products/info',
            "STOCK_URL": base + 'product_search/secure/v5/stocks',
            "TRANS": base + 'reporting/secure/v4/transactions',
            "HIST_URL": 'https://charting.vwdservices.com/hchart/v1/deGiro/data.js',
            "DICT_URL": base + 'product_search/config/dictionary/',
            "SEARCH_URL": base + 'product_search/secure/v5/products/lookup',
            "CHECK_ORDER_URL": base + 'trading/secure/v5/checkOrder;jsessionid={}',
            "ORDER_URL": base + 'trading/secure/v5/order/{};jsessionid={}',
            "ORDER_HIST_URL": base + 'reporting/secure/v4/order-history',
            "ACCOUNT_URL": base + 'reporting/secure/v6/accountoverview',
            "API_INFO": base + 'login/secure/config'
        }

    def login(self, reconnect=False):
        # prevents for duplicate logging attempts
        if not reconnect and self.init_account and self.degiro_id and self.degiro_api_urls:
            self.logger.info('Already logged in.')
            return True

        self.logger.info("Perform login with %s/******@%s", self.username,
                         self.api_urls["LOGIN_URL"])
        self.session_id = self.__get_session_id()
        if not self.session_id:
            self.logger.error("Authentication error")
            return False

        self.logger.info("login successful")
        # get account init token and id
        self.degiro_id, self.init_account = self.__get_int_account_and_id()
        if not self.init_account or not self.degiro_id:
            self.logger.error("account id or token is empty")
            return False
        if not self.read_config():
            self.logger.error("Could't create the degiro config object")
            return False
        self.degiro_api_urls = self.update_config()
        if not self.degiro_api_urls:
            self.logger.error("Could't load api infos")
            return False
        return True

    def is_logged_in(self):
        """
        Checks if already logged in
        :return: true if logged in otherwise false
        """
        if self.session_id and self.init_account and self.degiro_id:
            return True
        return False

    def __get_session_id(self):
        post_data = {
            'data': {
                "isPassCodeReset": False,
                "isRedirectToMobile": False,
                "queryParams": {},
                "username": self.username,
                "password": self.password
            },
            'headers': NetworkTool.DEFAULT_HEADER,
            'cookies': None
        }

        response = self.network_tool.post(self.api_urls["LOGIN_URL"], {}, post_data)
        if not response:
            return False
        # get session id
        return response.cookies.get('JSESSIONID')

    def __get_int_account_and_id(self):
        params = {
            "sessionId": self.session_id
        }

        response = self.network_tool.get(self.api_urls["CONFIG_URL"], params)
        if not response:
            self.logger.error("Couldn't collect account id and token")
            return False
        data = response.json()
        my_id = DictHelper.find_first_key('id', data)
        my_init_account = DictHelper.find_first_key('intAccount', data)
        return my_id, my_init_account

    def get_order_id_of_stock(self, stock: str, exchange: str):
        """

        :param stock:
        :param exchange:
        :return:
        """
        if not self.is_logged_in():
            return None
        params = {
            'searchText': stock,
            'limit': 3,
            'offset': 0,
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }
        response = self.network_tool.get(self.api_urls["SEARCH_URL"], params)
        if not response:
            self.logger.error("Couldn't collect product id")
            return False
        data = response.json()
        if "products" in data:
            for product in data["products"]:
                symbol_check = product["symbol"].lower() == stock.lower()
                exchange_id_check = product["exchangeId"] == str(Ch.get_exchange_id(exchange))
                if symbol_check and exchange_id_check:
                    return product["id"]
        return None

    def get_commission(self, price):
        return 2.0 + price * 0.00026

    def set_initial_cash(self, cash):
        raise NotImplementedError

    def delete(self, order_id: str):
        """
        Delete order by order id
        :param order_id:
        :return: True if status successful otherwise false
        """
        if not self.is_logged_in():
            return None
        params = {
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }
        self.logger.info("Delete order {}".format(order_id))
        delete_url = self.api_urls["ORDER_URL"].format(order_id, self.session_id)
        response = self.network_tool.delete(delete_url, params)
        if response.status_code == 200:
            success = response.json()["statusText"] == "success"
            if success:
                my_order = self.db_tool.session.query(Orders).\
                    filter(Orders.order_uuid == order_id).first()
                my_order.status = Status.deleted
                self.db_tool.commit()
            return success
        return False

    def get_open_orders(self):
        """
        Returns all open orders i.e. orders without close status like DELETE
        :return:
        """
        from_date = datetime.now() - timedelta(days=2)
        order_hist = self.get_order_history(from_date, datetime.now())
        created_items = [x for x in order_hist if x["status"] == "CONFIRMED" and
                         x["type"] == "CREATE"]
        filtered_list = []
        for created_item in created_items:
            item_to_add = False
            for item in order_hist:
                item_to_add = item
                if item["orderId"] == created_item["orderId"] and item["type"] == "DELETE":
                    item_to_add = None
                    break
            if item_to_add:
                filtered_list.append(item_to_add)
        return filtered_list

    def get_order_history_all(self):
        # the order history is limited by 90 days so we have to limit our from/to date
        data = []
        idx = 0
        while True:
            to_date = datetime.now() - relativedelta(days=91*idx)
            from_date = (to_date - relativedelta(days=90))
            new_data = self.get_order_history(from_date, to_date, "", "")
            if not new_data:
                break
            idx += 1
            data += new_data

        # at first we need all delete items to filter data
        delete_data = [item["orderId"] for item in data if item["type"] == "DELETE" and
                       item["status"] == "CONFIRMED"]
        portfolio = [item for item in data if item.get("orderId", False)
                     not in delete_data and item["status"] == "CONFIRMED"]
        return portfolio

    def get_order_history(self, from_date: datetime, to_date: datetime,
                          filter_status="CONFIRMED", order_type="CREATE"):
        """
        Returns the order history between date range
        :param from_date: start date
        :param to_date: end date
        :param filter_status: filter history by status for example CONFIRMED
        :param order_type: : filter history by type for example CREATE
        :return:
        """
        if not self.is_logged_in():
            return None

        params = {
            'fromDate': from_date.strftime("%d/%m/%Y"),
            'toDate': to_date.strftime("%d/%m/%Y"),
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }
        response = self.network_tool.get(self.api_urls["ORDER_HIST_URL"], params)
        if response.status_code == 200:
            data = response.json()["data"]
            if filter_status and order_type:
                return [x for x in data if x["status"] == filter_status and x["type"] == order_type]
            return data
        return None

    def get_transaction_history(self, from_date: datetime, to_date: datetime):
        """

        :param from_date:
        :param to_date:
        :return:
        """
        if not self.is_logged_in():
            return None

        params = {
            'fromDate': from_date.strftime("%d/%m/%Y"),
            'toDate': to_date.strftime("%d/%m/%Y"),
            'groupTransactionsByOrder': True,
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }
        response = self.network_tool.get(self.api_urls["TRANS"], params)
        if response.status_code == 200:
            data = response.json()["data"]
            return data
        return None

    def buy(self, stock_id: int, exchange: str, order_data: dict):
        order_data['buySell'] = 'BUY'
        return self.__order(stock_id, exchange, order_data)

    def sell(self, stock_id: int, exchange: str, order_data: dict):
        order_data['buySell'] = 'SELL'
        return self.__order(stock_id, exchange, order_data)

    def __order(self, stock_symbol: str, exchange: str, order_data):
        """

        :param stock_symbol:
        :param exchange:
        :param order_data
        :return:
        """
        if not self.is_logged_in():
            return None
        amount = order_data["size"]
        # we need the productId to issue an order
        degiro_order_data = None
        price = 0
        tz = TraderBase.get_timezone()
        my_stock = self.db_tool.session.query(Stock).filter(Stock.id == stock_id).first()
        if my_stock is None:
            raise RuntimeError("Stock with symbol {} is unknown.".format(stock_symbol))
        my_order = Orders(
                status=Status.confirmed,
                size=order_data["size"] * -1 if order_data["buySell"] == "SELL" else order_data["size"],
                stock_id=my_stock.id,
                signal_id=order_data.get('signal_id'),
                is_sell=True if order_data["buySell"] == "SELL" else False,
                date=datetime.now(tz)
                )
        my_order.expire_date = datetime.combine(date.today(), datetime.max.time())
        if order_data["orderType"].value == OrderType.market.value:
            degiro_order_data = {
                "buySell": order_data["buySell"],
                "orderType": self.DegiroOrderType.market.value,
                "productId": self.get_order_id_of_stock(stock_symbol, exchange),
                "size": amount,
                "timeType": self.DegiroTimeType.intraDay.value
            }
            my_order.order_type = OrderType.market
        elif order_data["orderType"].value == OrderType.limit.value:
            degiro_order_data = {
                "buySell": order_data["buySell"],
                "orderType": self.DegiroOrderType.limit.value,
                "productId": self.get_order_id_of_stock(stock_symbol, exchange),
                "size": amount,
                "price": round(order_data["price"], 2),
                "timeType": self.DegiroTimeType.intraDay.value
            }
            my_order.order_type = OrderType.limit
            my_order.price = round(order_data["price"], 2)
            price = round(order_data["price"], 2)
        else:
            raise NotImplementedError("unknown order type")
        # execute check order
        post_data = {
            'data': degiro_order_data,
            'headers': NetworkTool.DEFAULT_HEADER,
            'cookies': None
        }

        params = {
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }
        # confirm order
        response = self.network_tool.post(self.api_urls["CHECK_ORDER_URL"].format(self.session_id),
                                          params, post_data)
        data = response.json()
        if response.status_code == 200 and data['statusText'] == "success":
            self.logger.info("Confirm order {} of {}x{}".format(stock_symbol, amount, price))
            url_buy = self.api_urls["ORDER_URL"].format(data["confirmationId"], self.session_id)
            response = self.network_tool.post(url_buy, params, post_data)
            # execute order
            data = response.json()
            if response.status_code == 200 and data['statusText'] == "success":
                self.logger.info("Order {} of {}x{} successfull".format(stock_symbol, amount,
                                                                        price))
                portfolio = self.get_portfolio_object()
                my_order.status = Status.confirmed
                my_order.order_uuid = data["orderId"]
                portfolio.orders.append(my_order)
                self.db_tool.commit()
                return data["orderId"]
        else:
            self.logger.error(data)
        return None

    def get_data(self, data: dict):
        """
        Asks degiro web api for data
        :param data:
        :return:
        """
        if not self.is_logged_in():
            return None
        post_data = {
            'data': data,
            'headers': NetworkTool.DEFAULT_HEADER,
            'cookies': None
        }
        params = {
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }
        response = self.network_tool.post(self.api_urls["PRODUCT_URL"], params, post_data)
        if response:
            return response.json()
        return None

    def get_day(self, issueid, time_zone='Europe/Berlin', days=1, resolution='PT1S'):
        """
        Get today data for stock
        :param issueid: stock id
        :param time_zone:
        :param days:
        :param resolution:
        :return: sqlalchemy series object
        """
        return self.get_series(issueid, resolution=resolution, period='P%sD' % days,
                               time_zone=time_zone)

    def get_week(self, issueid, time_zone='Europe/Berlin'):
        """
        Get week data for stock
        :param issueid: stock id
        :param time_zone:
        :param resolution:
        :return: sqlalchemy series object
        """
        return self.get_series(issueid, resolution='P1D', period='P1W', time_zone=time_zone)

    def get_month(self, issueid, resolution='P1D', time_zone='Europe/Berlin'):
        """
        Get month data for stock
        :param issueid:
        :param resolution: P1D or P1W
        :param time_zone:
        :return:
        """
        return self.get_series(issueid, resolution=resolution, period='P1M', time_zone=time_zone)

    def get_year(self, issueid, years='1', resolution='P1D', time_zone='Europe/Berlin'):
        """
        Get year data for stock
        :param issueid:
        :param years: 1 for one year 2 for two years ...
        :param resolution: P1D, P1W or P1M
        :param time_zone:
        :return:
        """
        return self.get_series(issueid, resolution=resolution, period='P%sY' % years,
                               time_zone=time_zone)

    def get_series(self, issueid, resolution, period, time_zone):
        """

        :param issueid:
        :param resolution: PT1S, PT1M, PT5M , PT15M, PT60M, P1D, P1W, P2W, P1M, P1Y minimal
        resolution seems to be 1
        minute
        :param period: P1D, P1W, P2W, P1M, P1Y
        :param time_zone:
        :return: series objects or None if no data present
        """
        # intraday data has only p1d period
        if resolution.startswith('PT1S'):
            period = 'P1D'

        params = {
            'requestid': 1,
            'resolution': resolution,
            'culture': 'en-US',
            'period': period,
            # 'series': ['issueid:%s' % issueid, 'price:issueid:%s' % issueid,
            #  'volume:issueid:%s' % issueid, 'ohlc:issueid:%s' % issueid],
            'series': ['issueid:%s' % issueid, 'volume:issueid:%s' % issueid,
                       'ohlc:issueid:%s' % issueid],
            'format': 'json',
            'userToken': self.degiro_id,
            'tz': time_zone
        }
        response = self.network_tool.get(self.api_urls["HIST_URL"], params)
        if response:
            return DegiroDataHelper.series_to_object(response.json())
        return None

    def get_issue_ids_by_degiro_id(self, degiro_ids):
        """
        This method can be used for evaluating index issue ids
        because the degiro config contains a list with all indices degiro ids
        :param degiro_ids:
        :return: list with issue ids
        """
        issue_ids = []
        data = self.get_data(degiro_ids)
        if data and 'data' in data:
            data = data['data']
            for degiro_id in degiro_ids:
                if str(degiro_id) in data and 'vwdId' in data[str(degiro_id)]:
                    issue_ids.append(data[str(degiro_id)]['vwdId'])
        return issue_ids

    def get_issue_ids_by_stock_symbol(self, symbols):
        """
        This method generates a search query and returns the issue id by symbol
        :param symbols:
        :return: list with issue ids
        """
        if not self.is_logged_in():
            return None
        issue_ids = []
        for symbol in symbols:
            params = {
                'searchText': symbol,
                'limit': 7,
                'offset': 0,
                'intAccount': self.init_account,
                'sessionId': self.session_id
            }

            response = self.network_tool.get(self.api_urls["SEARCH_URL"], params)
            data = None
            if response:
                data = response.json()

            if data and 'products' in data:
                data = response.json()
                for result in data['products']:
                    if 'symbol' in result and result['symbol'] == symbol and 'vwdId' in result:
                        issue_ids.append(result['vwdId'])
                        break
        return issue_ids

    def get_all_stocks_of_country(self, country_sym, limit=25, as_json=False):
        """
        Returns all stocks of given country sym
        :param country_sym: country symbol (DE, FR)
        :param limit: request item limit
        :param as_json: set to true if you need json data
        :return:
        """
        if not self.is_logged_in():
            return None
        country_id = Ch.get_country_id(country_sym)
        stock_list = []
        if not country_id:
            raise ValueError("Invalid country symbol")

        offset = 0
        response_fail_ctx = 0
        while response_fail_ctx <= 5:

            params = {
                'intAccount': self.init_account,
                'limit': limit,
                'offset': offset,
                'requireTotal': 'true',
                'searchText': '',
                'sessionId': self.session_id,
                'sortColumns': 'name',
                'sortTypes': 'asc',
                'stockCountryId': country_id
            }

            response = self.network_tool.get(self.api_urls["STOCK_URL"], params)
            if response:
                data = response.json()
                if 'products' not in data or not data['products']:
                    break
                offset += limit
                for stock in data['products']:
                    if as_json:
                        stock_list.append(stock)
                    else:
                        my_stock = DegiroDataHelper.stock_to_object(stock, None, None)
                        if my_stock is not None:
                            stock_list.append(my_stock)
            else:
                response_fail_ctx += 1
                if response_fail_ctx == 5:
                    self.logger.error("Detect bad behavior during data collection")
                    break
        return stock_list

    def __get_cdax_stocks(self, limit, as_json):
        stock_list = []
        # iterate over germany and filter isin that starts with
        german_stock_gen = self.get_all_stocks_of_country('DE', limit, as_json)
        for german_stock in german_stock_gen:
            stock_list.append(DegiroDataHelper.
                              stock_to_object_filter(german_stock, 'CDAX', 'de', self.db_tool))
        return stock_list

    def __get_index_stocks(self, index_sym, limit, as_json):
        stock_list = []
        index_id = Ch.get_id_of_index_symbol(index_sym, ignore_product=True)
        offset = 0
        total = 1
        while total > offset:

            params = {
                'intAccount': self.init_account,
                'limit': limit,
                'offset': offset,
                'requireTotal': 'true',
                'searchText': '',
                'sessionId': self.session_id,
                'sortColumns': 'name',
                'sortTypes': 'asc',
                'indexId': index_id
            }
            data = None
            response = self.network_tool.get(self.api_urls["STOCK_URL"], params)
            if response:
                data = response.json()

            if data is None or \
                    'products' not in data or \
                    'total' not in data or not data['products']:
                self.logger.warning("Got an empty stock data result for %s: %s with params %s",
                                    index_sym, data, json.dumps(params))
                break

            if total == 1:
                total = data['total']

            for stock in data['products']:
                if as_json:
                    stock_list.append(stock)
                else:
                    my_stock = DegiroDataHelper.stock_to_object(stock, index_sym, self.db_tool)

                    if self.__is_not_inside(my_stock, stock_list):
                        offset += 1
                        stock_list.append(my_stock)
                    else:
                        return stock_list
        return stock_list

    def get_all_stocks_of_index(self, index_sym, limit=25, as_json=False):
        """

        :param limit: sets the yield size
        :param indices_syms: list with indices symbols i.e. ['SDAX', 'MDAX']
        :param as_json: if true function returns a json dict otherwise a database object
        :return: list of stocks
        """
        if not self.is_logged_in():
            return None
        stock_list = []
        if index_sym == 'CDAX':
            stock_list = self.__get_cdax_stocks(limit, as_json)
        else:
            stock_list = self.__get_index_stocks(index_sym, limit, as_json)
        if not stock_list:
            raise RuntimeError("Couldn't get stocks of index")
        return stock_list

    def read_config(self):
        """
        Reads the degiro config
        :return: true if succeeded otherwise false
        """
        params = {
            'intAccount': self.init_account,
            'sessionId': self.session_id
        }

        response = self.network_tool.get(self.api_urls["DICT_URL"], params)
        Ch.DEGIRO_CONFIG = response.json()
        return Ch.DEGIRO_CONFIG is not None

    def update_config(self):
        """
        Reads the degiro config
        :return: true if succeeded otherwise false
        """
        data = {
            'data': {},
            'headers': self.network_tool.DEFAULT_HEADER,
            'cookies': {'jsessionid': self.session_id}
        }
        response = self.network_tool.get(self.api_urls["API_INFO"], None, data)
        if response:
            return response.json()
        return None

    def get_last_price(self, stock, time_zone='Europe/Berlin'):
        """
        Returns last price of stock
        :param stock: stock symbol
        :param time_zone:
        :return: last price
        """
        params = {
            'requestid': 1,
            'resolution': 'PT1S',
            'culture': 'en-US',
            'period': 'P1D',
            'series': ['issueid:%s' % stock.get_degiro_id()],
            'format': 'json',
            'userToken': self.degiro_id,
            'tz': time_zone
        }
        result = self.network_tool.get(self.api_urls["HIST_URL"], params)
        if result:
            data = result.json()['series'][0]['data']
            if data and 'lastPrice' in data:
                return data['lastPrice']
        return None

    @staticmethod
    def __is_not_inside(my_stock, stock_list):
        if not my_stock:
            return False
        for stock in stock_list:
            if stock[1].name == my_stock[1].name:
                return False
        return True

