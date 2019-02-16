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
import urllib

import unidecode

from autotrader.base.dict_helper import DictHelper
from autotrader.base.network_tool import NetworkTool
from autotrader.base.string_compare_helper import StringCompareHelper


class WeBullClient:
    """
    Client for the webull database
    """

    WEBULL_BASE_URL = "http://securitiesapi.stocks666.com/api"
    WEBULL_STOCK_URL = WEBULL_BASE_URL + "/securities/stock/%s"
    WEBULL_COMP_BRIEF = WEBULL_STOCK_URL + "/compBrief"
    # ETR:RIB
    WEBULL_SYMBOL_TO_TICKER_ID = WEBULL_BASE_URL + "/stocks/ticker/googleFinancial/tickerIdMapping"
    # 913261697
    WEBULL_STOCK_DATA = WEBULL_BASE_URL + "/securities/ticker/v2/%s"
    WEBULL_STOCK_RECOMMENDATION = WEBULL_STOCK_URL + "/recommendation"
    WEBULL_STOCK_INCOME = WEBULL_STOCK_URL + "/statementsv2"
    WEBULL_STOCK_SHEET = WEBULL_STOCK_URL + "/statementsV2Detail"
    WEBULL_INCOME_ANALYSIS = WEBULL_STOCK_URL + "/incomeAnalysis/crucial"
    WEBULL_SEARCH = WEBULL_BASE_URL + '/search/tickers5'
    KEY_PRICE_TARGET = 'priceTarget'
    KEY_MEAN = 'mean'
    KEY_HIGH = 'high'
    KEY_LOW = 'low'
    KEY_CURRENT = 'current'
    KEY_RATING = 'rating'
    KEY_MEASURES = 'measures'
    KEY_ATTR = 'attr'
    KEY_VALUE = 'value'
    KEY_EPS = 'eps'
    KEY_CPS = 'cps'
    KEY_TRENDS = 'trends'
    KEY_AGE = 'age'
    KEY_ANALYSTS_COUNT = 'NumberOfAnalysts'
    KEY_DISTR = 'distributionList'
    KEY_REC_COUNT = 'Recommendation'

    def __init__(self, logger: logging.Logger):
        self.network_tool = NetworkTool(logger)
        self.logger = logger
        self.network_tool = NetworkTool(self.logger)

    def deep_search(self, stock, index):
        """
        Searches with more information's
        :param stock:
        :param index: index symbol
        :return:
        """
        stock_infos = [stock.name]
        if stock.symbol > stock.name:
            stock_infos.append(stock.symbol)
        part = stock.name.replace("ü", "ue").replace("Ü", "ue").replace("ä", "ae").\
            replace("Ä", "ae").replace("ö", "oe").replace('-', " ").\
            replace("Ö", "oe").replace('&', '').replace('.', '').split(' ')

        part_2 = stock.name.replace("ü", "u").replace("Ü", "u").replace("ä", "a").\
            replace("Ä", "a").replace("ö", "o").replace('-', ' ').\
            replace("Ö", "o").replace('&', '').replace('.', '').split(' ')

        if part:
            stock_infos.append(part[0])
        if len(part) >= 2:
            stock_infos.append(part[0] + ' ' + part[1])

        if len(part) >= 3:
            stock_infos.append(part[0] + ' ' + part[1] + ' ' + part[2])

        if part_2:
            stock_infos.append(part_2[0])
        if len(part_2) >= 2:
            stock_infos.append(part_2[0] + ' ' + part_2[1])
        if len(part_2) >= 3:
            stock_infos.append(part_2[0] + ' ' + part_2[1] + ' ' + part_2[2])

        prefer_exchange = None
        if index in ['CAC 40']:
            prefer_exchange = ['FRA']
        elif index in ['DAX', 'MDAX', 'SDAX', 'CDAX']:
            prefer_exchange = ['FRA', 'ETR']
        elif index in ['FTSE 100']:
            prefer_exchange = ['LON']
        elif index in ['OMX Helsinki 15', 'OMX Helsinki 25']:
            prefer_exchange = ['HEL']
        elif index in ['DOW JONES', 'NASDAQ 100', 'NASDAQ 100', 'S&P 100', 'S&P 500']:
            prefer_exchange = ['NYSE', 'NSQ', 'NAS']
        data = self.search_query(stock_infos, symbol=stock.symbol, prefer_exchange=prefer_exchange)
        return data

    def search(self, name, prefer_exchange=None):
        """
        Search for stock by name
        :param name: stock name
        :param prefer_exchange: prefer exchange
        :return: json data
        """
        return self.search_query([name], prefer_exchange=prefer_exchange)

    def search_query(self, names, symbol=None, prefer_exchange=None):
        """
        Search for stock by name
        :param names: list of stock infos
        :param symbol: symbol
        :param prefer_exchange: prefer exchange
        :return: json data
        """
        datas = []
        max_score = []
        for name in names:
            unaccented_name = unidecode.unidecode(name)
            unaccented_name = unaccented_name[:(min(len(unaccented_name), 14))]
            if name == 'AXA':
                symbol = 'AXA'
            elif name == 'METRO Wholesale & Food Specialist AG':
                unaccented_name = 'Metr'
            elif name == 'Bouygues':
                symbol = 'BYG'
            elif name == 'ARCELORMITTAL':
                symbol = 'AARD'
            elif name == 'Garmin Ltd':
                unaccented_name = 'Garmin'
            elif name == 'Lauder (Estee) Co':
                unaccented_name = 'Estee Lauder'
                symbol = 'EL'
            response = self.network_tool.get(
                WeBullClient.WEBULL_SEARCH,
                {
                    'keys': unaccented_name,
                    'hasNumber': 0,
                    'clientOrder': 3,
                    'queryNumber': 30
                }
            )
            if not response:
                continue

            datas_return = response.json()
            if 'list' not in datas_return:
                continue

            datas_tmp = [data_return for data_return in datas_return['list'] if data_return['template'] == 'stock']
            for data in datas_tmp:
                ratio = StringCompareHelper.levenshtein_ratio_and_distance(data['name'].lower(),
                                                                           unaccented_name.lower())
                if symbol:
                    ratio += StringCompareHelper.levenshtein_ratio_and_distance(data['symbol'].lower(), symbol.lower())/2

                if prefer_exchange and (data['exchangeCode'] in prefer_exchange or
                                        data['disExchangeCode'] in prefer_exchange):
                    max_score.append(ratio+2)
                else:
                    max_score.append(ratio)
            datas += datas_tmp

        if not max_score:
            self.logger.error("Couldn't collect data for  {}".format(', '.join(names)))
            return None

        return datas[max_score.index(max(max_score))]

    def get_ticker_ids(self, symbols: list):
        """
        Converts symbols to webull ticker ids
        http://securitiesapi.stocks666.com/api/stocks/ticker/googleFinancial/tickerIdMapping?symbols=ETR:RIB
        :param symbols: a list of stock symbols [ETR:ADS,ETR:RIB]
        :return: webull ticker ids
        """
        params = {
            'symbols': ','.join(symbols)
        }

        fix_syms = [['XET:', 'ETR:'], ['NDQ:', 'NASDAQ:'], ['NSY:', 'NYSE:'],
                    ['LSE:', 'LON:'], ['HSE:', 'HEL:'], ['EPA:', 'FRA:']]

        for fix_sym in fix_syms:
            params['symbols'] = params['symbols'].replace(fix_sym[0], fix_sym[1])

        response = self.network_tool.get(WeBullClient.WEBULL_SYMBOL_TO_TICKER_ID, params)
        if not response:
            self.logger.error("Couldn't collect account id and token")
            return False
        data = response.json()
        ticker_dict = {}
        for d in data:
            key = '%s:%s' % (d['sourceExchangeCode'], d['tickerSymbol'])

            for fix_sym in fix_syms:
                key = key.replace(fix_sym[1], fix_sym[0])
            ticker_dict[key] = d['tickerId']
        return ticker_dict

    def get_recommendation(self, ticker_id):
        """
        Returns recommendation data for stock
        :param ticker_id: webull ticker id
        :return: json data
        """
        response = self.network_tool.get(
            WeBullClient.WEBULL_STOCK_RECOMMENDATION % ticker_id,
            {}
        )
        if not response:
            self.logger.error("Couldn't collect recommendation data for ", ticker_id)
            return False
        data = response.json()
        return data

    def get_income(self, ticker_id):
        """
        Returns income data for stock
        :param ticker_id: webull ticker id
        :return: json data
        """
        response = self.network_tool.get(
            WeBullClient.WEBULL_STOCK_SHEET % ticker_id,
            {}
        )
        if not response:
            self.logger.error("Couldn't collect income data for ", ticker_id)
            return False
        data = response.json()
        return data

    def get_income_analysis(self, ticker_id):
        """
        Returns income analysis data for stock
        :param ticker_id: webull ticker id
        :return: json data
        """
        response = self.network_tool.get(
            WeBullClient.WEBULL_INCOME_ANALYSIS % ticker_id,
            {}
        )
        if not response:
            self.logger.error("Couldn't collect income analysis data for ", ticker_id)
            return False
        data = response.json()
        return data

    def get_company_brief(self, ticker_id):
        """
        Returns company brief data for stock
        :param ticker_id: webull ticker id
        :return: json data
        """
        response = self.network_tool.get(
            WeBullClient.WEBULL_COMP_BRIEF % ticker_id,
            {}
        )
        if not response:
            self.logger.error("Couldn't collect company brief data for ", ticker_id)
            return False
        data = response.json()
        return data

    def get_industries(self, ticker_id):
        """
        Returns a list of industries
        :param ticker_id: webull ticker id
        :return: list of industries
        """
        company_brief = self.get_company_brief(ticker_id)
        tags = [val for val in DictHelper.find_key('context', company_brief,
                                                   [('attr', 'industry')])]
        if tags:
            tags = tags[0].replace('  ', ' ')
            tags = tags.split(' - ')
        return tags

    def get_region(self, ticker_id):
        """
        Returns region of stock
        :param ticker_id: webull ticker id
        :return: region
        """
        company_brief = self.get_company_brief(ticker_id)
        address = [val for val in DictHelper.find_key('context', company_brief,
                                                   [('attr', 'address')])]
        if address:
            return address[0].split(', ')[-1]
        return None

    def get_sheet(self, ticker_id, sheet_id, query_size=300):
        """
        Returns financial sheet(income, balance, cash flow) data for stock
        :param ticker_id: webull ticker id
        :param sheet_id: income=1, balance=2 and chasflow = 3
        :param query_size:
        :return:
        """
        params = {
            "queryNumber": query_size,
            "type": sheet_id
        }
        response = self.network_tool.get(
            WeBullClient.WEBULL_STOCK_SHEET % ticker_id,
            params
        )
        if not response:
            self.logger.error("Couldn't collect sheet data for ", ticker_id)
            return False
        data = response.json()
        return data
