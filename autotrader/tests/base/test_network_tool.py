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
import unittest
import logging
from autotrader.base.network_tool import NetworkTool

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestNetworkTool(unittest.TestCase):
    """
    Tests the base network tool
    """

    @staticmethod
    def test_network():
        """
        fires some get and post requests
        :return: nothing
        """
        network_tool = NetworkTool(TEST_LOGGER)
        data_default = {'data': None, 'headers': NetworkTool.DEFAULT_HEADER, 'cookies': None}

        data_firefox = {'data': None, 'headers': NetworkTool.DEFAULT_HEADER, 'cookies': None}

        assert network_tool.get(None, None, None) is None
        response = network_tool.get("http://www.google.de", None, None)
        assert response
        response = network_tool.get("http://www.google.de", None, data_default)
        assert response
        response = network_tool.get("http://www.google.de", None, data_firefox)
        assert response
        post_data = {
            'data': {'number': 12524, 'type': 'issue', 'action': 'show'},
            'headers': NetworkTool.FIREFOX_HEADER,
            'cookies': None
        }
        response = network_tool.post(
            "http://bugs.python.org",
            None,
            post_data
        )
        assert response
        response = network_tool.post(
            None,
            None,
            None
        )
        assert response is None


if __name__ == '__main__':
    unittest.main()
