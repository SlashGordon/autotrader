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
from sqlalchemy import Column, String, Float, Integer, Table, BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


BASE = declarative_base()


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


class TagApp(BASE):
    """
    Sqlalchemy object for stock representation
    """

    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    tag = Column(String(250), nullable=False, unique=True)
    category = Column(String(15), nullable=False)
    stocks = relationship("StockApp", secondary=tag_to_stock, back_populates="tags")


class IndexApp(BASE):
    """
    Sqlalchemy object for index representation
    """
    __tablename__ = 'index'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(250), unique=True)
    stocks = relationship("StockApp", secondary=index_to_stock, back_populates="indices")

    def __repr__(self):
        return "Index(id=%r,symbol=%r)" % (self.id, self.symbol)


class StockApp(BASE):
    """
    Sqlalchemy object for stock representation
    """
    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(250))
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(15), nullable=False)
    indices = relationship("IndexApp", secondary=index_to_stock, back_populates="stocks")
    tags = relationship("TagApp", secondary=tag_to_stock, back_populates="stocks")

    def __repr__(self):
        return "Stock(id=%r,symbol=%r)" % (self.id, self.symbol)


class SeriesApp(BASE):
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
    stock_id = Column(Integer, ForeignKey('stock.id'), nullable=True)
    index_id = Column(Integer, ForeignKey('index.id'), nullable=True)
    currency = Column(String(15), nullable=False)
    stock = relationship("StockApp", backref="series")
    index = relationship("IndexApp", backref="series")
    __table_args__ = (UniqueConstraint('date', 'stock_id', name='_date_stock_series_uc'),)

    def __repr__(self):
        return "Series(id=%r,priceopen=%r)" % (self.id, self.priceopen)


class FilterApp(BASE):
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
    stock = relationship("StockApp", backref="filter")

    def __repr__(self):
        return "filter(id=%r,name=%r,value=%r)" % (self.id, self.name, self.value)


class SignalApp(BASE):
    """
    Sqlalchemy object for signal representation
    """
    __tablename__ = 'signal'

    id = Column(Integer, primary_key=True)
    profit_in_percent = Column(Float)
    date = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(40), nullable=False)
    info = Column(String(80))
    status = Column(Integer, nullable=False)
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("StockApp", backref="signal")

    def __repr__(self):
        return "Signal(id=%r,name=%r,profit_in_percent=%r)" % \
               (self.id, self.name, self.profit_in_percent)


class ParameterApp(BASE):
    """
    Sqlalchemy object for parameter representation
    """

    __tablename__ = 'parameter'

    id = Column(Integer, primary_key=True)
    value = Column(Float)
    signal_id = Column(Integer, ForeignKey('signal.id'))
    signal = relationship("SignalApp", backref="parameter")

    def __repr__(self):
        return "Parameter(id=%r,value=%r)" % (self.id, self.value)


class PortfolioApp(BASE):
    """
    Database depot object
    """

    __tablename__ = 'portfolio'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    user = Column(String(40), nullable=False)
    cash = Column(Float)
    initial_cash = Column(Float)


class OrdersApp(BASE):
    """
    Sqlalchemy object for orders representation
    """

    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    size = Column(Integer, nullable=False)
    price = Column(Float, default=-1)
    commission = Column(Float, default=-1)
    stock_id = Column(Integer, ForeignKey('stock.id'))
    stock = relationship("StockApp", backref="orders")
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship("PortfolioApp", backref="orders")

    def __repr__(self):
        return "Orders(id=%r,type=%r, size=%r)" % (self.id, self.order_type, self.size)
