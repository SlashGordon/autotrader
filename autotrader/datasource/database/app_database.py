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
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from autotrader.datasource.database.app_schema import BASE


class StockDataBaseApp:
    """
    Autotrader database client
    """

    url = 'sqlite:///app.db'

    def __init__(self, logger: logging.Logger):
        self.engine = None
        self.session = None
        self.db_session = None
        self.logger = logger

    def connect(self):
        """
        Connect to the database
        :param database: name of database to connect
        :return: nothing
        """
        if not self.session:
            self.engine = create_engine(StockDataBaseApp.url)
            self.db_session = sessionmaker(bind=self.engine)
            self.session = self.db_session()

    def is_connected(self):
        """
        Checks if database connection is established
        :return: true if connection to database is established otherwise false
        """
        return self.session is not None

    def create(self):
        """
        Creates a database by given name
        :return:
        """
        if self.engine:
            if os.path.exists('app.db'):
                os.remove('app.db')
            BASE.metadata.create_all(self.engine)
            return True
        return False

    def close(self):
        """
        Closes current session
        :return:
        """
        if self.session:
            self.session.close()
