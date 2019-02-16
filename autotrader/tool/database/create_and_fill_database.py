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
from autotrader.broker.degiro.degiro_data_helper import DegiroDataHelper
from autotrader.datasource.database.stock_schema import Stock, Exchange, Index, LookupTable, Region
from autotrader.datasource.webull_client import WeBullClient
from autotrader.datasource.yahoo_finance_client import YahooFinanceClient


class CreateAndFillDataBase:
    """
    Database installer
    """

    def __init__(self, config, arguments: dict, logger: logging.Logger):
        self.logger = logger
        self.config = config
        self.history = self.config['autotrader']['max_history']
        self.indices_list = self.config['autotrader']['indices'].split(',')
        self.db_tool = arguments["db_tool"]
        self.drop_data = arguments.get('drop_data', True)
        self.client = arguments['datasource']

    def set_indices(self, indices):
        """
        Sets indices list
        :param indices:
        :return:
        """
        self.indices_list = indices

    def build(self):
        """
        Starts the database installation
        :return:
        """
        if self.drop_data:
            self.db_tool.drop()
            self.db_tool.create()
        self.db_tool.connect()
        self.client.read_config()

        # create exchanges
        exchanges = DegiroDataHelper.exchange_to_object()
        # TODO: sync new exchanges with database
        if self.drop_data:
            for exchange in exchanges:
                self.logger.info("Add exchange %s to db" % exchange.name)
                self.db_tool.session.add(exchange)
        # create indices
        indices = []
        yah = YahooFinanceClient(self.logger)
        for index in self.indices_list:
            index_obj = Index(
                symbol=index,
                feed_quality="15M"
                )

            self.logger.info("Add Index %s to db" % index_obj.symbol)
            series = yah.get_series(index_obj.symbol, 'P%sY' % self.history)
            if series is None:
                raise RuntimeError("Could not get index data")
            for row in series:
                index_obj.series.append(row)
            indices.append(index_obj)
            self.db_tool.session.add(index_obj)
        self.client.login()

        for index in indices:
            stocks = []
            idx = 0
            # try to get all stocks of index with a refresh of degiro session if necessary.
            while not stocks and idx < 6:
                try:
                    stocks = self.client.get_all_stocks_of_index(index.symbol)
                except RuntimeError:
                    self.logger.warning("Couldn't get stocks of index %s. Start try %s with re login.", index, idx)
                    self.client.login(True)
                    idx += 1

            if not stocks:
                raise RuntimeError("Couldn't get stocks of index")

            regions = {}
            for region_db in self.db_tool.session.query(Region):
                regions[region_db.region] = region_db
            last_region = None
            # add stocks to exchanges
            for stock_and_vwd_id in stocks:
                # add degiro lookup
                vwdId = stock_and_vwd_id[0]
                stock = stock_and_vwd_id[1]
                lookup_degiro = LookupTable(
                    lookup_id=vwdId,
                    type='degiro'
                )
                stock.lookup.append(lookup_degiro)
                stock_in_db = self.db_tool.session.query(Stock).filter(Stock.name == stock.name).\
                    first()
                if stock_in_db:
                    self.logger.info("Stock already in db. Add stock %s:%s to index." %
                                     (index.symbol, stock.symbol))
                    index.stocks.append(stock_in_db)
                else:
                    self.logger.info("Add stock %s:%s to db" % (index.symbol, stock.symbol))
                    # fill lookup
                    # 1. webull
                    bull = WeBullClient(self.logger)
                    bull_data = bull.deep_search(stock, index.symbol)
                    if bull_data and 'tickerId' in bull_data:
                        region = bull.get_region(bull_data['tickerId'])

                        if not region:
                            self.logger.error("%s:%s region search failed"
                                              % (index.symbol, stock.symbol))
                            region = last_region
                        else:
                            last_region = region

                        if region not in regions:
                            regions[region] = Region(
                                region=region
                            )
                        lookup = LookupTable(
                            lookup_id=bull_data['tickerId'],
                            type='webull'
                        )
                        regions[region].stocks.append(stock)
                        stock.lookup.append(lookup)
                    else:
                        self.logger.error("%s:%s webull search failed"
                                          % (index.symbol, stock.symbol))
                    # create stock
                    exchange = self.db_tool.session.query(Exchange).\
                        filter(Exchange.id == stock.exchange_id).first()
                    exchange.stock_exchange.append(stock)
                    index.stocks.append(stock)
                    # add data to stocks
                    self.logger.info("Add data to %s:%s" % (index.symbol, stock.symbol))
                    data = self.client.get_year(vwdId, years=int(self.history))
                    if data is not None:
                        for series in data:
                            stock.series.append(series)
                    else:
                        self.logger.warning("Data is None for %s:%s" % (index.symbol, stock.symbol))
            self.db_tool.commit()
        self.db_tool.session.close()
        return 0
