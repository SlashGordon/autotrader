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
from autotrader.indicators.oscillators.stochastic import \
    Stochastic
from autotrader.indicators.oscillators.stochastic_m_2 import \
    StochasticM2
from autotrader.indicators.oscillators.stochastic_m_3 import \
    StochasticM3
from autotrader.tests.indicators.test_base import TestBase


class TestSO(TestBase):
    """
    Tests the Stochastic Oscillator strategy
    """

    @staticmethod
    def test_1_run_100():
        """
        Checks if results are stable. The method must produce same values after n runs.
        """
        TestBase.test_strategy = Stochastic
        TestBase.test_params = [3, 4, 5]
        TestBase.check_consistency()
        TestBase.test_strategy = StochasticM2
        TestBase.test_params = [3, 4, 5]
        TestBase.check_consistency()
        TestBase.test_strategy = StochasticM3
        TestBase.test_params = [3, 4, 5]
        TestBase.check_consistency()

    @staticmethod
    def test_2_gen_signal():
        """
        Tests two stocks with freezed data set
        """
        TestBase.test_strategy = Stochastic
        TestBase.test_excepted_results = [(0.2911, 1), (-0.0039, 1), (0.0031, -1), (-0.1044, -1)]
        TestBase.test_params = [[5, 5, 10], [20, 20, 40]]
        TestBase.compare_excepted_with_results()
        TestBase.test_strategy = StochasticM2
        TestBase.test_excepted_results = [(0.6483, 1), (-0.0039, 1), (0.0021, -1), (-0.1088, -1)]
        TestBase.test_params = [[5, 5, 10], [20, 20, 40]]
        TestBase.compare_excepted_with_results()
        TestBase.test_strategy = StochasticM3
        TestBase.test_excepted_results = [(0.2911, 1), (-0.0039, 1), (0.0010, -1), (-0.0039, -1)]
        TestBase.test_params = [[5, 5, 10], [20, 20, 40]]
        TestBase.compare_excepted_with_results()


if __name__ == '__main__':
    unittest.main()
