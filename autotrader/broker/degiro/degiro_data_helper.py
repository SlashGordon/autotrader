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

from autotrader.datasource.database.stock_schema import Exchange, Stock, Series
from autotrader.broker.degiro.degiro_config_helper import DegiroConfigHelper


class DegiroDataHelper:
    """
    Helper class for degiro config file
    """
    SERIES_DATA_COLUMNS = ['prices', 'open', 'high', 'low', 'close', 'volume', 'date']

    @staticmethod
    def exchange_to_object():
        """
        Transforms json exchange data to sqlalchemy object
        :return: exchange sqlalchemy object
        """
        exchanges_list = []
        exchange_data = DegiroConfigHelper.DEGIRO_CONFIG["exchanges"]
        for exchange in exchange_data:
            if all(my_key in exchange for my_key in
                   ["id", "name", "country", "city", "code", "hiqAbbr"]):
                exchanges_list.append(
                    Exchange(
                        id=exchange["id"],
                        name=exchange["name"],
                        country=exchange["country"],
                        city=exchange["city"],
                        symbol=exchange["code"],
                        symbol_short=exchange["hiqAbbr"]
                    )
                )
        return exchanges_list

    @staticmethod
    def stock_to_object(stock, index_sym, db_tool):
        """
        Transforms json stock data to sqlalchemy object
        :param stock:
        :param index_sym:
        :param db_tool
        :return: with stock sqlalchemy object
        """
        if all(my_key in stock for my_key in
               ["exchangeId", "symbol", "name", "category", "vwdId", "feedQuality"]):
            return stock["vwdId"], Stock(
                exchange_id=stock['exchangeId'],
                symbol=stock['symbol'],
                name=stock['name'],
                category=stock['category'],
                feed_quality=stock['feedQuality']
            )
        return None

    @staticmethod
    def stock_to_object_filter(data, index_sym, isin, db_tool):
        """
        Transforms json stock list data to sqlalchemy objects. The data is filtered by isin.
        :return: stock sqlalchemy object list
        """
        stock_list = []
        for stock in data['products']:
            if 'isin' in stock and stock['isin'].lower().startswith(isin) and 'vwdId' in stock:
                my_stock = DegiroDataHelper.stock_to_object(stock, index_sym, db_tool)
                if my_stock is not None:
                    stock_list.append(
                        my_stock
                    )
        return stock_list

    @staticmethod
    def series_to_object(data):
        """
        Transforms json series data to sqlalchemy object
        :return: with stock sqlalchemy object
        """
        if 'series' in data and len(data['series']) >= 2 and \
           'data' in data['series'][1] and 'data' in data['series'][2]:
            volumes = data['series'][1]['data']
            ohlcs = data['series'][2]['data']
            starttime = datetime.datetime.strptime(data['start'], '%Y-%m-%dT%H:%M:%S')
            series_list = []
        else:
            return None
        # start converter
        for idx, volume in enumerate(volumes):
            ohlc = ohlcs[idx]
            fulldate = starttime + datetime.timedelta(days=volume[0])
            resolution = data['resolution']
            if resolution == 'PT1H':
                resolution = 'PT60M'
            if resolution.startswith('PT') and resolution.endswith('M'):
                fulldate = starttime + datetime.timedelta(minutes=volume[0])
            if resolution == 'PT1S':
                fulldate = starttime + datetime.timedelta(seconds=volume[0])
            series_list.append(
                Series(
                    priceopen=ohlc[1],
                    pricehigh=ohlc[2],
                    pricelow=ohlc[3],
                    priceclose=ohlc[4],
                    volume=volume[1],
                    resolution=resolution,
                    date=fulldate
                )
            )
        return series_list
