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


class DegiroConfigHelper:
    """
    Helper class for degiro config file
    """

    DEGIRO_CONFIG = {}

    @staticmethod
    def get_exchange_id(exchange_sym):
        """
        Returns the degiro id of exchange symbol (xetra, fra)
        :param exchange_sym:
        :return:
        """
        try:
            id = [x['id'] for x in DegiroConfigHelper.DEGIRO_CONFIG["exchanges"]
                  if 'id' in x and 'micCode' in x and x['micCode'] == exchange_sym][0]
            return id
        except KeyError:
            return None

    @staticmethod
    def get_country_id(country_sym):
        """
        Returns the degiro id of country symbol (DE, US)
        :param country_sym:
        :return:
        """
        try:
            return [x['id'] for x in DegiroConfigHelper.DEGIRO_CONFIG["countries"]
                    if 'id' in x and 'name' in x and x['name'] == country_sym][0]
        except KeyError:
            return None

    @staticmethod
    def get_country_id_indices(country_sym):
        """
        Get all indices as id by country symbol.
        :param country_sym: country symbol
        :return: a list of index ids
        """
        try:
            country_id = DegiroConfigHelper.get_country_id(country_sym)
            indices = [x for x in DegiroConfigHelper.DEGIRO_CONFIG["stockCountries"]
                       if 'id' in x and x['id'] == country_id][0]['indices']
            product_ids = []
            # replace with product id
            for index in indices:
                for index_2 in DegiroConfigHelper.DEGIRO_CONFIG["indices"]:
                    if index_2['id'] == index and 'productId' in index_2:
                        product_ids.append(index_2['productId'])
            return product_ids
        except KeyError:
            return None

    @staticmethod
    def get_country_sym_indices(country_sym):
        """
        Get all indices as symbol by country symbol.
        :param country_sym: country symbol
        :return: a list of index symbols
        """
        try:
            index_ids = DegiroConfigHelper.get_country_id_indices(country_sym)
            indices = DegiroConfigHelper.DEGIRO_CONFIG['indices']
            syms = [x['name'] for x in indices if  x['id'] in index_ids or 'productId' in x
                    and x['productId'] in index_ids]
            return syms
        except KeyError:
            return None

    @staticmethod
    def get_id_of_index_symbol(index_sym, ignore_product=False):
        """
        Get the id of an index symbol
        :param index_sym: dax, mdax
        :param ignore_product: set to true if you need the product ids
        :return: symbol of index
        """
        try:
            indices = DegiroConfigHelper.DEGIRO_CONFIG['indices']
            sym_id = [x['productId'] if 'productId' in x and not ignore_product else x['id']
                      for x in indices if 'name' in x and x['name'] == index_sym][0]
            return sym_id
        except KeyError:
            return None
