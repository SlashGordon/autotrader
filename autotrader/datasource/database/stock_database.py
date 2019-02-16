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
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from autotrader.datasource.database.stock_schema import BASE


class StockDataBase:
    """
    Autotrader database client
    """
    def __init__(self, sql_config, logger: logging.Logger):
        self.engine = None
        self.session = None
        self.db_session = None
        self.sessions = {}
        self.__sessions = {}
        self.logger = logger
        self.sql_config = sql_config

    def connect(self, database=None):
        """
        Connect to the database
        :param database: name of database to connect
        :return: nothing
        """
        if database is None:
            database = self.sql_config['database']
        if not self.session:
            url = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(self.sql_config['user'],
                                                          self.sql_config['pw'],
                                                          self.sql_config['address'],
                                                          self.sql_config['port'],
                                                          database)
            # MySQL features an automatic connection close behavior,
            # for connections that have been idle for eight hours or more.
            # To circumvent having this issue, use the pool_recycle
            # option which controls the maximum age of any connection:
            self.engine = create_engine(url, pool_recycle=3600)
            self.db_session = sessionmaker(bind=self.engine)
            self.session = self.db_session()

    def is_connected(self):
        """
        Checks if database connection is established
        :return: true if connection to database is established otherwise false
        """
        return self.session is not None

    def create(self, database=None):
        """
        Creates a database by given name
        :param url: sql url
        :param database: database name to create
        :return:
        """
        if database is None:
            database = self.sql_config['database']

        url = 'mysql+pymysql://{}:{}@{}:{}'.format(self.sql_config['user'],
                                                   self.sql_config['pw'],
                                                   self.sql_config['address'],
                                                   self.sql_config['port'])
        # MySQL features an automatic connection close behavior,
        # for connections that have been idle for eight hours or more.
        # To circumvent having this issue, use the pool_recycle
        # option which controls the maximum age of any connection:
        self.engine = create_engine(url, pool_recycle=3600)
        if self.engine and database:
            # create db if not exist
            try:
                self.engine.execute("CREATE DATABASE IF NOT EXISTS {}".format(database))
            except SQLAlchemyError:
                self.logger.exception("Error during create:")
                return False
            self.engine.execute("USE {}".format(database))
            BASE.metadata.create_all(self.engine)
        return True

    def delete(self, db_session_object):
        if db_session_object in self.session.new:
            self.session.expunge(db_session_object)
        else:
            self.session.delete(db_session_object)

    def commit(self, error_counter=0):
        """

        :return:
        """
        try:
            self.session.commit()
            return
        except BrokenPipeError or SQLAlchemyError:
            self.logger.warning("Error during commit error count {}.".format(error_counter))
            if error_counter > 5:
                error_counter += 1
                time.sleep(100)
                self.session.connect()
                self.commit(error_counter)
                return
        raise RuntimeError("Commit was not successful")

    def close(self):
        """
        Closes current session
        :return:
        """
        if self.session:
            self.session.close()

    def drop(self, database=None):
        """
        Drop an existing database
        :param database: name of database
        :return:
        """
        if database is None:
            database = self.sql_config['database']
        url = 'mysql+pymysql://{}:{}@{}:{}'.format(self.sql_config['user'],
                                                   self.sql_config['pw'],
                                                   self.sql_config['address'],
                                                   self.sql_config['port'])
        # MySQL features an automatic connection close behavior,
        # for connections that have been idle for eight hours or more.
        # To circumvent having this issue, use the pool_recycle
        # option which controls the maximum age of any connection:
        self.engine = create_engine(url, pool_recycle=3600)
        if self.engine and database:
            # create db if not exist
            try:
                sql_statement = "DROP DATABASE IF EXISTS {}".format(database)
                self.engine.execute(sql_statement)
            except SQLAlchemyError:
                self.logger.exception("Error during drop:")
