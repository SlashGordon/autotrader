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
import time
from datetime import datetime
import logging


import re
from dateutil.relativedelta import relativedelta
from autotrader.datasource.database.stock_schema import Series
from autotrader.base.network_tool import NetworkTool


class YahooFinanceClient:
    """
    Starting on May 2017, Yahoo financial has terminated its service on
    the well used EOD data download without warning. This is confirmed
    by Yahoo employee in forum posts.
    Yahoo financial EOD data, however, still works on Yahoo financial pages.
    These download links uses a "crumb" for authentication with a cookie "B".
    This code is provided to obtain such matching cookie and crumb.
    """

    HISTORY_URL = 'https://l1-query.finance.yahoo.com/v8/finance/chart/%s'

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.network_tool = NetworkTool(logger)
        # Cookie and corresponding crumb
        self._cookie = {}
        self._crumb = None

    def set_crumb(self):
        """
        Get the crumb by fake query. Crumb is mandatory and used for future requests.
        :return: true if succeeded otherwise false
        """
        get_data = {'data': None, 'headers': NetworkTool.FIREFOX_HEADER, 'cookies': None}
        response = self.network_tool.get('https://finance.yahoo.com/quote/^GSPC', {}, get_data)
        if response:
            alines = response.content.decode('utf-8')
            crumb_store = alines.find('CrumbStore')
            crumb = alines.find('crumb', crumb_store + 10)
            crumb_key = alines.find(':', crumb + 5)
            crumb_key_start = alines.find('"', crumb_key + 1)
            crumb_key_end = alines.find('"', crumb_key_start + 1)
            crumb = alines[crumb_key_start + 1:crumb_key_end]
            self._crumb = crumb
            self._cookie = response.cookies.get_dict()
            self.logger.info("Collect crumb %s" % self._crumb)
            return True
        self.logger.exception("Didnt find any crumb")
        return False

    @staticmethod
    def __fix_symbol(symbol):
        if symbol == 'DAX':
            symbol = '%5EGDAXI'
        elif symbol == 'MDAX':
            symbol = '%5EMDAXI'
        elif symbol == 'SDAX':
            symbol = '%5ESDAXI'
        elif symbol == 'CDAX':
            symbol = '%5ECDAXX'
        elif symbol == 'TECDAX':
            symbol = '%5ETECDAX'
        elif symbol == 'FTSE 100':
            symbol = '%5EFTSE'
        elif symbol == 'OMX Helsinki 15':
            symbol = '%5EOMXH15'
        elif symbol == 'OMX Helsinki 25':
            symbol = '%5EOMXH25'
        elif symbol == 'CAC 40':
            symbol = '%5EFCHI'
        elif symbol == 'DOW JONES':
            symbol = '%5EDJI'
        elif symbol == 'NASDAQ 100':
            symbol = '%5EIXIC'
        elif symbol == 'NIKKEI 225':
            symbol = '%5EN225'
        elif symbol == 'S&P 100':
            symbol = '%5EOEX'
        elif symbol == 'S&P 500':
            symbol = '%5EGSPC'
        elif symbol == 'BEL 20':
            symbol = '%5EBFX'
        elif symbol == 'IBEX 35':
            symbol = '%5EIBEX'
        elif symbol == 'AEX':
            symbol = '%5EAEX'
        elif symbol == 'ASX 200':
            symbol = '%5EAXJO'
        elif symbol == 'OMX Stockholm 30':
            symbol = '%5EOMX'
        elif symbol == 'Switzerland 20':
            symbol = '%5ESSMI'
        return symbol

    @staticmethod
    def __create_date(period_str):
        date_back = None
        match = re.match(r"^P(\d+)(\w)$", period_str)
        if match and match.group(1) and match.group(2):
            back = int(match.group(1))
            period_symbol = str(match.group(2)).lower()
            if period_symbol == 'd':
                date_back = datetime.now() + relativedelta(days=-back)
            elif period_symbol == 'w':
                date_back = datetime.now() + relativedelta(weeks=-back)
            elif period_symbol == 'm':
                date_back = datetime.now() + relativedelta(months=-back)
            elif period_symbol == 'y':
                date_back = datetime.now() + relativedelta(years=-back)
        return date_back

    def get_series(self, symbol: str, period: str, as_json=False):
        """
        Creates a series object by given index/stock symbol
        :param symbol: symbol dax, mdax, i7n usw.
        :param period: P1D, P1W, P2W, P1M, P1Y
        :param as_json: switch to enable json output
        :return: series objects or None if no data present
        """
        # Check to make sure that the cookie and crumb has been loaded
        if not self._crumb:
            self.set_crumb()
        # fix symbol name because dax is in yahoo finance world ^daxi
        symbol = self.__fix_symbol(symbol)
        # Prepare the parameters and the URL
        date_back = self.__create_date(period)
        if date_back is None:
            self.logger.error("The period string %s is not valid", period)
            return None
        time_start = time.mktime(date_back.timetuple())
        time_end = time.mktime(datetime.now().timetuple())
        params = {
            'period1': int(time_start),
            'period2': int(time_end),
            'interval': '1d',
            'includeTimestamps': True,
            'includePrePost': True,
            'events': 'earn',
            'corsDomain': 'de.finance.yahoo.com'

        }
        self._cookie['ucs'] = 'eup=2&pnid=&pnct='
        get_data = {'data': None, 'headers': NetworkTool.FIREFOX_HEADER, 'cookies': self._cookie}
        response = self.network_tool.get(YahooFinanceClient.HISTORY_URL % symbol, params, get_data)
        if response:
            # Perform the query
            # There is no need to enter the cookie here, as it is automatically handled by opener
            data = response.json()
            if as_json:
                return data
            return self.series_to_object(data)
        return None

    @staticmethod
    def series_to_object(data):
        """
        Transforms the json response to sqlalchemy object.
        :param data: json response
        :return: sqlalchemy object
        """
        series_list = []
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            data = data['chart']['result'][0]
            if 'timestamp' in data and 'indicators' in data and 'quote' in data['indicators'] \
                    and data['indicators']['quote']:
                times = data['timestamp']
                quote = data['indicators']['quote'][0]
                for idx, my_time in enumerate(times):
                    series_list.append(
                        Series(
                            priceopen=quote['open'][idx],
                            pricehigh=quote['high'][idx],
                            pricelow=quote['low'][idx],
                            priceclose=quote['close'][idx],
                            volume=quote['volume'][idx],
                            resolution='P1D',
                            date=datetime.fromtimestamp(my_time)
                        )
                    )
        return series_list
