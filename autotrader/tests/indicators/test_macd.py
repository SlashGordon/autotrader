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
from autotrader.indicators.trend.macd_histogram import MacdHistogramSignal as Macd
from autotrader.tests.indicators.test_base import TestBase


class TestMacd(TestBase):
    """
    Test for simple macd histogram strategy
    """

    @staticmethod
    def test_1_run_100():
        """
        Checks if results are stable. The method must produce same values after n runs.
        """
        TestBase.test_strategy = Macd
        TestBase.test_params = [7, 20, 4]
        TestBase.check_consistency()

    @staticmethod
    def test_2_gen_signal():
        """
        Tests two stocks with freezed data set
        """
        TestBase.test_excepted_results = [(0.04639, -1), (0.01784, -1), (-0.1223, 1), (-0.2319, 1)]
        TestBase.test_params = [[7, 20, 4], [8, 16, 5]]
        TestBase.compare_excepted_with_results()


if __name__ == '__main__':
    unittest.main()
