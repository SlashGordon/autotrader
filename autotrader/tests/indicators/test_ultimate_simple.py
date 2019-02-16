# -*- coding: utf-8 -*-
""" Autotrader

 Copyright 2017-2017 Slash Gordon

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
from autotrader.indicators.oscillators.ultimate_simple_ema import \
    UltimateSimple
from autotrader.tests.indicators.test_base import TestBase


class TestUMS(TestBase):
    """
    Tests the ultimate simple strategy
    """

    @staticmethod
    def test_1_run_100():
        """
        Checks if results are stable. The method must produce same values after n runs.
        """
        TestBase.test_strategy = UltimateSimple
        TestBase.test_params = [20, 30, 49]
        TestBase.check_consistency()

    @staticmethod
    def test_2_gen_signal():
        """
        Tests two stocks with freezed data set
        """
        TestBase.test_excepted_results = [(0.29866, -1), (0.2066, -2), (0.0480, 1), (-0.19280, -1)]
        TestBase.test_params = [[72, 79, 90], [6, 9, 39]]
        TestBase.compare_excepted_with_results()


if __name__ == '__main__':
    unittest.main()
