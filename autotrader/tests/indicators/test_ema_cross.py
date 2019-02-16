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
from autotrader.indicators.averages.ema_cross_signal import EmaCrossSignal
from autotrader.tests.indicators.test_base import TestBase


class TestEma(TestBase):
    """
    Test for simple exponential average crossing signal strategy
    """

    @staticmethod
    def test_1_run_100():
        """
        Checks if results are stable. The method must produce same values after n runs.
        """
        TestBase.test_strategy = EmaCrossSignal
        TestBase.test_params = [72, 79]
        TestBase.check_consistency()

    @staticmethod
    def test_2_gen_signal():
        """
        Tests two stocks with freezed data set
        """
        TestBase.test_excepted_results = [(-0.0039, 1), (0.40143, 1), (-0.0633, -1), (-0.3326, 2)]
        TestBase.test_params = [[72, 79], [6, 9]]
        TestBase.compare_excepted_with_results()


if __name__ == '__main__':
    unittest.main()
