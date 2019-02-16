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
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import zlib
import base64
import json
from sqlalchemy import Column, String, Float, Integer, JSON, Boolean, Enum, LargeBinary, Table, BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

BARS_SERIES = 0
BARS_PANDAS = 1
BARS_NUMPY = 2
BASE = declarative_base()


class Exchange(BASE):
    """
    Sqlalchemy object for exchange representation
    """
    __tablename__ = 'exchange'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)
    symbol_short = Column(String(5), nullable=False)

    def __repr__(self):
        return "Exchange(id=%r,symbol=%r)" % (self.id, self.name)


class Category(enum.Enum):
    """
    Enum for categories
    """
    index = 0
    stock = 1


# association table for many to many relation between stocks and indices
index_to_stock = Table('index_to_stock', BASE.metadata,
    Column('index_id', Integer, ForeignKey('index.id')),
    Column('stock_id', Integer, ForeignKey('stock.id'))
)

# association table for many to many relation between stocks and tags
tag_to_stock = Table('tag_to_stock', BASE.metadata,
    Column('tag_id', Integer, ForeignKey('tag.id')),
    Column('stock_id', Integer, ForeignKey('stock.id'))
)


class Tag(BASE):
    """
    Sqlalchemy object for stock representation
    """

    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    tag = Column(String(250), nullable=False, unique=True)
    category = Column(String(15), nullable=False)
    stocks = relationship("Stock", secondary=tag_to_stock, back_populates="tags")


class SeriesItem:

    id = Column(Integer, primary_key=True)
    feed_quality = Column(String(250), nullable=False)

    def get_bars(
            self,
            start=datetime.now() + timedelta(days=-365*10),
            end=datetime.now(),
            output_type=0,
            resolution='P1D'
    ):
        """
        Returns bars of a stock
        :param start:
        :param end:
        :param output_type:
        :param resolution:
        :return:
        """
        session = Session.object_session(self)
        if not start or not end or not resolution or not session:
            return None
        # this must be an query !!!!!!! Do not iterate/filter over self.series
        series = session.query(Series)\
            .filter(Series.stock_id == self.id) \
            .filter(Series.resolution == resolution) \
            .filter(Series.date.between(start, end)).all()
        if output_type == BARS_PANDAS:
            data_frame = pd.DataFrame([[i.priceclose, i.priceopen, i.volume, i.pricehigh,
                                        i.pricelow, i.date
                                        ] for i in series], columns=['Close', 'Open', 'Volume',
                                                                     'High', 'Low', 'Date'])
            data_frame = data_frame.set_index(pd.DatetimeIndex(data_frame['Date'].dt.date))
            return data_frame
        elif output_type == BARS_NUMPY:
            return np.asarray([[i.priceclose,
                                i.priceopen,
                                i.volume,
                                i.pricehigh,
                                i.pricelow,
                                i.date
                               ] for i in series])
        return series


class Index(BASE, SeriesItem):
    """
    Sqlalchemy object for index representation
    """
    __tablename__ = 'index'

    symbol = Column(String(250), unique=True)
    stocks = relationship("Stock", secondary=index_to_stock, back_populates="indices")

    def __repr__(self):
        return "Index(id=%r,symbol=%r)" % (self.id, self.symbol)


class LookupTable(BASE):

    __tablename__ = 'lookup_table'

    id = Column(Integer, primary_key=True)
    lookup_id = Column(String(100), nullable=False)  # not unique because of NASDAQ:DISCK/DISCA issue
    type = Column(String(50))
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("Stock", backref="lookup")


class Region(BASE):

    __tablename__ = 'region'

    id = Column(Integer, primary_key=True)
    region = Column(String(100), nullable=False, unique=True)


class Stock(BASE, SeriesItem):
    """
    Sqlalchemy object for stock representation
    """
    __tablename__ = 'stock'

    symbol = Column(String(250))
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(15), nullable=False)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=True)
    exchange = relationship("Exchange", backref="stock_exchange")
    region_id = Column(Integer, ForeignKey('region.id'))
    region = relationship("Region", backref="stocks")
    indices = relationship("Index", secondary=index_to_stock, back_populates="stocks")
    tags = relationship("Tag", secondary=tag_to_stock, back_populates="stocks")

    def __repr__(self):
        return "Stock(id=%r,symbol=%r)" % (self.id, self.symbol)

    def get_data(self, key):
        """
        Returns company data by key
        :param key:
        :return:
        """
        for data in self.jsondata:
            if data.name == key:
                return data.data
        return None

    def __get_data_id(self, type):
        for look in self.lookup:
            if look.type == type:
                return look.lookup_id
        return None

    def get_degiro_id(self):
        """
        Returns degiro lookup id for stock
        :return: id
        """
        return self.__get_data_id('degiro')

    def get_webull_id(self):
        """
        Returns webull lookup id for stock
        :return: id
        """
        return self.__get_data_id('webull')

    def get_data_attr(self, key, attr, annual=False, quarter_diff=0):
        """
        Get company data by key and attr
        :param key:
        :param attr:
        :param annual:
        :param quarter_diff:
        :return:
        """
        datas = self.get_data(key)
        if key == 'recommendation':
            if attr == 'rating' and 'rating' in datas:
                return float(datas['rating'])
            if 'measures' in datas:
                for strut in datas['measures']:
                    if 'attr' in strut and 'value' in strut and strut['attr'] == attr:
                        try:
                            return float(strut['value'])
                        except ValueError:
                            return -1
        else:

            for idx, data in enumerate(datas):
                if quarter_diff == 0 or idx >= quarter_diff:
                    if not annual or annual and 'annual' in data and data['annual']:
                        if 'struts' in data:
                            for strut in data['struts']:
                                if 'attr' in strut and 'value' in strut and strut['attr'] == attr:
                                    try:
                                        return float(strut['value'])
                                    except ValueError:
                                        return -1
        return -1


class Series(BASE):
    """
    Sqlalchemy object for series representation
    """
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    priceopen = Column(Float)
    priceclose = Column(Float)
    pricehigh = Column(Float)
    pricelow = Column(Float)
    volume = Column(BigInteger, nullable=True)
    date = Column(DateTime)
    resolution = Column(String(15), nullable=False)
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=True)
    index_id = Column(Integer, ForeignKey('index.id'), nullable=True)
    stock = relationship("Stock", backref="series")
    index = relationship("Index", backref="series")
    __table_args__ = (UniqueConstraint('date', 'stock_id', 'resolution',
                                       name='_date_stock_series_uc'),)

    def __repr__(self):
        return "Series(id=%r,priceopen=%r)" % (self.id, self.priceopen)


class Filter(BASE):
    """
    Sqlalchemy object for filter representation
    """
    __tablename__ = 'filter'

    id = Column(Integer, primary_key=True)
    value = Column(Float)
    date = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(40), nullable=False)
    status = Column(Integer, nullable=False)
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("Stock", backref="filter")

    def __repr__(self):
        return "filter(id=%r,name=%r,value=%r)" % (self.id, self.name, self.value)


class Signal(BASE):
    """
    Sqlalchemy object for signal representation
    """
    __tablename__ = 'signal'

    id = Column(Integer, primary_key=True)
    profit_in_percent = Column(Float)
    probability = Column(Float)
    probability_30 = Column(Float)
    date = Column(DateTime(timezone=True), server_default=func.now())
    refresh_date = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(40), nullable=False)
    info = Column(String(80))
    status = Column(Integer, nullable=False)
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("Stock", backref="signal")

    def __repr__(self):
        return "Signal(id=%r,name=%r,profit_in_percent=%r)" % \
               (self.id, self.name, self.profit_in_percent)


class Parameter(BASE):
    """
    Sqlalchemy object for parameter representation
    """

    __tablename__ = 'parameter'

    id = Column(Integer, primary_key=True)
    value = Column(Float)
    signal_id = Column(Integer, ForeignKey('signal.id'))
    signal = relationship("Signal", backref="parameter")

    def __repr__(self):
        return "Parameter(id=%r,value=%r)" % (self.id, self.value)


class Plot(BASE):
    """
    Sqlalchemy object for plot data
    """

    __tablename__ = 'plot'

    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey('signal.id'))
    # for plot data in viewer
    data = Column(LargeBinary(length=(2**32)-1))
    signal = relationship("Signal", backref="plot")

    def __repr__(self):
        return "PlotData(id=%r)" % self.id

    def get_plot(self):
        """
        Converts plot blob to plot object
        :return:
        """
        import binascii
        try:
            return json.loads(zlib.decompress(base64.b64decode(self.data)).decode('utf-8'))
        except binascii.Error:
            return None

    def add_plot_to_data(self, my_object):
        """
        Converts plot object to blob
        :param my_object:
        :return:
        """
        my_json_str = json.dumps(my_object)
        my_pack_str = base64.b64encode(zlib.compress(my_json_str.encode("utf-8"), 9))
        self.data = my_pack_str


class JsonData(BASE):
    """
    Sqlalchemy object for jsondata representation
    """

    __tablename__ = 'jsondata'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(40), nullable=False)
    data = Column(JSON)
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("Stock", backref="jsondata")

    def __repr__(self):
        return "JsonData(id=%r,name=%r)" % (self.id, self.name)


class Status(enum.Enum):
    """
    Enum for order status
    """
    completed = 0
    confirmed = 1
    deleted = 2
    open = 3
    expired = 4


class OrderType(enum.Enum):
    """
    Enum for order types
    """
    limit = 0
    market = 1
    stoploss = 2
    stoplimit = 3
    trailingstop = 4


class Portfolio(BASE):
    """
    Database depot object
    """

    __tablename__ = 'portfolio'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    user = Column(String(40), nullable=False)
    cash = Column(Float)
    initial_cash = Column(Float)


class Orders(BASE):
    """
    Sqlalchemy object for orders representation
    """

    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(Status), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    order_uuid = Column(String(36), nullable=False)
    size = Column(Integer, nullable=False)
    expire_date = Column(DateTime(timezone=True))
    # null is possible because of market order
    price = Column(Float, default=-1)
    commission = Column(Float, default=-1)
    price_complete = Column(Float, default=-1)
    is_sell = Column(Boolean, default=False)
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("Stock", backref="orders")
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship("Portfolio", backref="orders")
    signal_id = Column(Integer, ForeignKey('signal.id'))
    signal = relationship("Signal", backref="signal")
    orders_id = Column(Integer, ForeignKey('orders.id'))
    orders = relationship("Orders", remote_side=[id], backref="associated_orders")

    def __repr__(self):
        return "Orders(id=%r,type=%r, size=%r)" % (self.id, self.order_type, self.size)
