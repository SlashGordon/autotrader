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
import logging
from dateutil.relativedelta import relativedelta
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from autotrader.datasource.database.stock_schema import Stock, JsonData, Exchange, Series, Index, \
    Tag, LookupTable
from autotrader.datasource.webull_client import WeBullClient
from autotrader.datasource.yahoo_finance_client import YahooFinanceClient
from autotrader.tool.database.create_and_fill_database import CreateAndFillDataBase


class UpdateDataBaseStocks:
    """
    Update Tool for autotrader database
    """

    def __init__(self, config, arguments, logger: logging.Logger):
        self.logger = logger
        self.config = config
        self.arguments = arguments
        self.db_tool = arguments["db_tool"]
        self.client = arguments["datasource"]
        self.stocks = None
        self.indices = None
        self.arguments['indices'] = self.config['autotrader']['indices'].split(',')
        self.arguments['resolutions'] = self.config['autotrader']['resolutions'].split(',')

    def build(self):
        """
        Starts the update process
        :return: nothing
        """
        # connect to db and degiro broker
        self.db_tool.connect()
        self.client.read_config()
        self.client.login()
        stocks_to_update = self.arguments['stocks_to_update']
        update_stocks = self.arguments['update_stocks']
        update_sheets = self.arguments['update_sheets']
        # get all indices and check if we have to add missing indices
        self.__add_missing_indices()
        # add data to stocks
        if not stocks_to_update:
            return 1

        self.stocks = self.db_tool.session.query(Stock)
        self.indices = self.db_tool.session.query(Index)

        if update_stocks:
            # update issue id
            self.__update_lookup_id_degiro()
            self.__update_stocks()
            self.__update_indices()
        if update_sheets:
            self.__update_lookup_id_webull()
            self.update_stock_sheets()
        # store new values in database
        self.db_tool.commit()
        self.db_tool.session.close()
        return 0

    def update_stock_sheets(self):
        """
        Updates the income, balance, recommendation ...
        :return:
        """
        try:
            num_rows_deleted = self.db_tool.session.query(JsonData).delete()
            self.logger.info("Deleted %s rows in JsonData" % num_rows_deleted)
            self.db_tool.commit()
        except SQLAlchemyError:
            self.db_tool.session.rollback()
        bull = WeBullClient(self.logger)
        stocks = [stock for stock in self.stocks]
        for stock in stocks:
            wb_id_obj = self.db_tool.session.query(LookupTable).filter(LookupTable.type == 'webull').\
                filter(LookupTable.stock_id == stock.id).first()
            if not wb_id_obj:
                self.logger.error("Stock %s:%s has no webull id" %
                                  (stock.indices[0].symbol, stock.symbol))
                continue
            wb_id = wb_id_obj.lookup_id
            self.logger.info("Update stock sheets %s:%s" % (stock.indices[0].symbol, stock.symbol))
            analysis = JsonData(
                name="incomeanalysis",
                data=bull.get_income_analysis(wb_id)
            )
            income_facts = JsonData(
                name="incomefacts",
                data=bull.get_income(wb_id)
            )
            rec = JsonData(
                name="recommendation",
                data=bull.get_recommendation(wb_id)
            )
            income = JsonData(
                name="income",
                data=bull.get_sheet(wb_id, 1)
            )
            balance = JsonData(
                name="balance",
                data=bull.get_sheet(wb_id, 2)
            )
            cash = JsonData(
                name="cash",
                data=bull.get_sheet(wb_id, 3)
            )

            self.__add_industry(stock, bull, wb_id)
            self.__insert_or_merge(stock, analysis)
            self.__insert_or_merge(stock, income_facts)
            self.__insert_or_merge(stock, rec)
            self.__insert_or_merge(stock, income)
            self.__insert_or_merge(stock, balance)
            self.__insert_or_merge(stock, cash)
            self.db_tool.commit()

    def __insert_or_merge(self, stock, data):
        merge_obj = None
        for json in stock.jsondata:
            if data.name == json.name:
                merge_obj = json

        if merge_obj:
            data.id = merge_obj.id
            self.db_tool.session.merge(data)
        else:
            stock.jsondata.append(data)

    def __update_lookup_id_degiro(self):
        indices = self.arguments['indices']
        for index_sym in indices:
            idx = 0
            stocks_andvwd_id = []
            # try to get all stocks of indices with a refresh of degiro session if necessary.
            while not stocks_andvwd_id and idx < 6:
                try:
                    stocks_andvwd_id = self.client.get_all_stocks_of_index(index_sym)
                except RuntimeError:
                    self.logger.warning("Couldn't get stocks of indices %s. Start try %s with re login.",
                                        ', '.join(indices), idx)
                    self.client.login(True)
                    idx += 1

            if not stocks_andvwd_id:
                raise RuntimeError("Couldn't get stocks of indices.")

            mappings = []
            for stock_and_vwd_id in stocks_andvwd_id:
                vwdId = stock_and_vwd_id[0]
                stock = stock_and_vwd_id[1]
                stock_update = self.db_tool.session.query(Stock).filter(
                    stock.name == Stock.name).first()
                if not stock_update:
                    self.logger.warning("stock {} does not exist".format(stock.symbol))
                    # start to add new stock
                    exchange = self.db_tool.session.query(Exchange). \
                        filter(Exchange.id == stock.exchange_id).first()
                    index = self.db_tool.session.query(Index). \
                        filter(Index.symbol == index_sym).first()
                    index.stocks.append(stock)
                    exchange.stock_exchange.append(stock)
                    self.db_tool.commit()
                else:
                    look = self.db_tool.session.query(LookupTable).\
                        filter(LookupTable.stock_id == stock_update.id).\
                        filter(LookupTable.type == 'degiro').first()
                    if not look:
                        self.logger.error('Stock {} has no lookup entry.'.format(stock.name))
                        continue
                    mappings.append({'id': look.id, 'lookup_id': vwdId})
                self.db_tool.session.bulk_update_mappings(LookupTable, mappings)
                self.db_tool.commit()

    def __update_lookup_id_webull(self):
        webull_looks = self.db_tool.session.query(LookupTable).\
            filter(LookupTable.type == 'webull')
        bull = WeBullClient(self.logger)
        mappings = []
        for webull_look in webull_looks:
            stock = webull_look.stock
            index = webull_look.stock.indices[0]
            bull_data = bull.deep_search(stock, index.symbol)
            if not webull_look:
                self.logger.error('Stock {} has no lookup entry.'.format(stock.name))
                continue
            mappings.append({'id': webull_look.id, 'lookup_id': bull_data['tickerId']})
        self.db_tool.session.bulk_update_mappings(LookupTable, mappings)
        self.db_tool.commit()

    def __build_time_deltas(self, resolutions_of_stock, stock):
        # set default deltas and last date of series resolution type
        last_date = {}
        deltas = {}
        for resolution in self.arguments['resolutions']:
            if resolution == 'P1D':
                last_date[resolution] = datetime.datetime.now() + relativedelta(years=-5)
            elif resolution == 'PT1S':
                last_date[resolution] = datetime.datetime.now() + relativedelta(days=-1)
            else:
                last_date[resolution] = datetime.datetime.now() + relativedelta(days=-30)

            deltas[resolution] = datetime.datetime.now() - last_date[resolution]

        for resolution in resolutions_of_stock:
            latest_date = self.db_tool.session.query(Series). \
                filter(stock.id == Series.stock_id). \
                filter(resolution == Series.resolution).order_by(desc(Series.date)).first()
            if latest_date:
                last_date[resolution] = latest_date.date
                deltas[resolution] = datetime.datetime.now() - last_date[resolution]
        return last_date, deltas

    def __update_stocks(self):
        for stock in self.stocks:
            self.logger.info("Update stock %s:%s", stock.name, stock.indices[0].symbol)
            # we need last series object for each resolution type i.e. for P1D, PT1S ...
            last_date, deltas = self.__build_time_deltas(self.arguments['resolutions'], stock)
            # start update
            for resolution in self.arguments['resolutions']:
                delta = 1 if deltas[resolution].days == 0 else deltas[resolution].days
                data = self.client.get_day(stock.get_degiro_id(), days=delta, resolution=resolution)

                if not data:
                    self.logger.warning("No data for %s:%s with resolution %s",
                                        stock.indices[0].symbol,
                                        stock.symbol, resolution)
                    break

                for series in data:
                    if series.date > last_date[resolution]:
                        self.logger.debug("Add data to %s", (stock.name, stock.indices[0].symbol))
                        stock.series.append(series)
                    else:
                        self.logger.debug("Ignore data of stock %s. Already exists", series)
            self.db_tool.commit()

    def __update_indices(self):
        yah = YahooFinanceClient(self.logger)
        for index in self.indices:
            self.logger.info("Update index %s", index.symbol)
            last_date, deltas = self.__build_time_deltas(self.arguments['resolutions'], index)
            # start update
            for resolution in self.arguments['resolutions']:
                delta = 1 if deltas[resolution].days == 0 else deltas[resolution].days
                data = yah.get_series(index.symbol, 'P%iD' % delta)

                if not data:
                    self.logger.warning("No data for %s with resolution %s", index.symbol, resolution)
                    break

                for series in data:
                    if series.date > last_date[resolution]:
                        self.logger.debug("Add data to %s", index.symbol)
                        index.series.append(series)
                    else:
                        self.logger.debug("Ignore data of stock %s. Already exists", series)
            self.db_tool.commit()

    def __add_missing_indices(self):
        my_indices_in_config = self.config['autotrader']['indices'].split(',')
        my_indices_in_db = [x[0] if len(x) > 0 else None
                            for x in self.db_tool.session.query(Index.symbol).all()]
        indices_to_add = set(my_indices_in_config).difference(my_indices_in_db)
        arguments = {
            'db_tool': self.db_tool,
            'drop_data': False,  # skip install db. We only want to add new data.
            'datasource': self.client
        }
        self.logger.info('Add indices %s' % ', '.join(indices_to_add))
        tool = CreateAndFillDataBase(self.config, arguments, self.logger)
        tool.set_indices(indices_to_add)
        return tool.build()

    def __add_industry(self, stock, bull, wb_ids):
        for mytag in bull.get_industries(wb_ids):
            tags_in_stock = [stocktag.tag
                             for stocktag in stock.tags if stocktag.category == 'Industry']
            if mytag not in tags_in_stock:
                dbtag = self.db_tool.session.query(Tag) \
                    .filter(Tag.category == 'Industry') \
                    .filter(Tag.tag == mytag).first()
                if dbtag:
                    stock.tags.append(dbtag)
                else:
                    stock.tags.append(Tag(
                        tag=mytag,
                        category='Industry'
                    ))
