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
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class NetworkTool:
    """
    Little helper class for request operations
    """

    DEFAULT_HEADER = {
        'content-type': 'application/json'
    }

    FIREFOX_HEADER = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
    }

    CHROME_HEADER = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/61.0.3163.100 Safari/537.36'
    }

    def __init__(self, logger: logging.Logger):
        self.session = requests.Session()
        self.session = self.__requests_retry_session()
        self.logger = logger

    def post(self, url: str, params: dict, data: dict):
        """
        Helper method for post operations
        :param url: request url
        :param params: params added to url
        :param data: [data] post data for request , [headers]  request header,  [cookies] additional
         cookies
        :return:
        """
        return self.__request(url, params, data, 0)

    def delete(self, url: str, params: dict):
        """
        Helper method for delete operations
        :param url: request url
        :param params: [data] payload for request , [headers]  request header,  [cookies] additional
         cookies
        :return:
        """
        return self.__request(url, params, None, 2)

    def get(self, url: str, params: dict, data: dict = None):
        """
        Helper method for get operations
        :param url: request url
        :param params: params added to url
        :param data: [headers]  request header,  [cookies] additional
        :return:
        """
        if data is None:
            data = {'data': None, 'headers': self.DEFAULT_HEADER, 'cookies': None}
        return self.__request(url, params, data, 1)

    def __requests_retry_session(
            self,
            retries=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504)
    ):
        self.session = self.session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        return self.session

    @staticmethod
    def __get_arguments(data):
        if data:
            post_data = None if 'data' not in data else json.dumps(data['data'])
            cookies = None if 'cookies' not in data else data['cookies']
            headers = None if 'headers' not in data else data['headers']
            return post_data, cookies, headers
        return None, None, None

    def __request(self, url: str, params: dict, data: dict, request_type=0):
        post_data, cookies, header = self.__get_arguments(data)
        try:
            if url is not None:
                response = None
                if request_type == 0:
                    response = self.session.post(url,
                                                 params=params,
                                                 data=post_data,
                                                 headers=header,
                                                 cookies=cookies)
                elif request_type == 1:
                    response = self.session.get(url,
                                                params=params,
                                                headers=header,
                                                cookies=cookies)
                elif request_type == 2:
                    response = self.session.delete(url,
                                                   params=params,
                                                   headers=header,
                                                   cookies=cookies)

                if response and (response.status_code not in [200, 201]):
                    self.logger.error("Request has unsuccessful error code %s",
                                      response.status_code)
                    return None
                return response
        except requests.exceptions.Timeout:
            self.logger.exception("Reached timeout.")
        except requests.exceptions.TooManyRedirects:
            self.logger.exception("URL is invalid or wrong.")
        except requests.exceptions.RequestException:
            self.logger.exception("Fatal error.")
        return None
