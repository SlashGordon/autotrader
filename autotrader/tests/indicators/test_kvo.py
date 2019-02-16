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
from autotrader.indicators.oscillators.kvo import \
    Kvo
from autotrader.tests.indicators.test_base import TestBase


class TestKvo(TestBase):
    """
    Tests the Klinger Volume Oscillator
    """

    @staticmethod
    def test_1_run_100():
        """
        Checks if results are stable. The method must produce same values after n runs.
        """
        TestBase.test_strategy = Kvo
        TestBase.test_params = [5, 20, 13]
        TestBase.check_consistency()

    @staticmethod
    def test_2_gen_signal():
        """
        Tests two stocks with freezed data set
        """
        TestBase.test_excepted_results = [(-0.5433, -1), (-0.3229, -2), (-0.4498, 2), (-0.3280, -1)]
        TestBase.test_params = [[11, 20, 5], [20, 40, 12]]
        TestBase.compare_excepted_with_results()


if __name__ == '__main__':
    unittest.main()
