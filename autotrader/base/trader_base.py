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
import configparser
import logging
import os


class TraderBase:
    """
    Helper class for logging and config parsing
    """

    @staticmethod
    def get_timezone():
        """
        Return configured timezone or europe berlin as default
        :return:
        """
        from pytz import timezone
        from os import environ
        config = TraderBase.get_config()
        try:
            return timezone(config['autotrader']['time_zone'])
        except (configparser.NoSectionError, configparser.NoOptionError, KeyError, TypeError):
            if environ.get('TZ') is not None:
                return timezone(os.environ['TZ'])
        return timezone('Europe/Berlin')

    @staticmethod
    def setup_logger(name: str):
        """
        Setup the autotrader standard logger
        :param name: name of logger
        :return: instance of logger
        """
        logger = logging.getLogger(name)
        log_formatter = logging.Formatter("%(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s()]"
                                          " [%(levelname)-5.5s] %(message)s")
        file_handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                        "..", "%s_broker.log" % name), mode='w')
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        logger.debug("Logging Setup successful")
        return logger

    @staticmethod
    def get_config(configfile=None):
        """
        Returns the autotrader config file. The path to the config file can be set by environment
        variable CONFIG_FILE or a co
        :return:
        """
        config = configparser.ConfigParser()
        if configfile is None:
            configfile = os.environ.get('CONFIG_FILE')

        if configfile is None:
            configfile = os.path.join(os.path.abspath(os.path.join(__file__, os.pardir)), '..',
                                      '..', 'config.ini')
        if not os.path.exists(configfile):
            return None
        config.read(configfile)
        return config
