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
import logging

from autotrader.indicators.oscillators.stochastic import Stochastic


class StochasticM2(Stochastic):
    """
    The Stochastic Oscillator with mode 2
    """
    NAME = 'StochasticM2'
    SHORT_NAME = 'SOM2'

    ARGUMENTS = {
        'symbol': None,
        'bars': None,
        'parameters': Stochastic.ARGUMENTS['parameters'],
        'optimizable': False,
        'name': NAME,
        'plot_result': False
    }

    def __init__(self, arguments: dict, logger: logging.Logger):
        arguments['mode'] = 2
        super(StochasticM2, self).__init__(arguments, logger)
