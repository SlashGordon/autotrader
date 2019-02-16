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

from autotrader.datasource.database.stock_schema import Stock
from autotrader.datasource.webull_client import WeBullClient as Bull

TEST_LOGGER = logging.getLogger()
TEST_LOGGER.setLevel(logging.WARNING)


class TestWebullClient(unittest.TestCase):
    """
    Test for the webull client
    """

    @staticmethod
    def check_recommendation(js_rec):
        """
        Checks the recommendation data for consistent
        :param js_rec:
        :return:
        """
        assert Bull.KEY_MEASURES in js_rec
        eps = -1
        cps = -1
        for measure in js_rec[Bull.KEY_MEASURES]:
            assert Bull.KEY_ATTR in measure
            assert Bull.KEY_VALUE in measure
            if measure[Bull.KEY_ATTR] == Bull.KEY_EPS:
                eps = float(measure[Bull.KEY_VALUE])
            elif measure[Bull.KEY_ATTR] == Bull.KEY_CPS:
                cps = float(measure[Bull.KEY_VALUE])
        assert eps > 0
        assert cps > 0
        assert Bull.KEY_PRICE_TARGET in js_rec
        assert Bull.KEY_CURRENT in js_rec[Bull.KEY_PRICE_TARGET]
        assert Bull.KEY_HIGH in js_rec[Bull.KEY_PRICE_TARGET]
        assert Bull.KEY_LOW in js_rec[Bull.KEY_PRICE_TARGET]
        assert Bull.KEY_MEAN in js_rec[Bull.KEY_PRICE_TARGET]
        assert Bull.KEY_RATING in js_rec
        assert Bull.KEY_TRENDS in js_rec
        for trend in js_rec[Bull.KEY_TRENDS]:
            assert Bull.KEY_AGE in trend
            assert Bull.KEY_DISTR in trend
            assert len(trend[Bull.KEY_DISTR]) == 5
            for distribution in trend[Bull.KEY_DISTR]:
                assert Bull.KEY_ANALYSTS_COUNT in distribution
                assert Bull.KEY_REC_COUNT in distribution

    @staticmethod
    def test_symbol_to_ticker():
        """
        Tests the api
        """
        # Garmin Ltd GRMN NASDAQ
        # 3M MMM S&P 500
        webull = Bull(TEST_LOGGER)
        gr = Stock(name='Garmin Ltd ', symbol='GRMN')
        gr_data = webull.deep_search(gr, 'NASDAQ')
        assert gr_data and gr_data['symbol'] == 'GRMN'
        tlg = Stock(name='TLG Immobilien', symbol='TLG')
        tlg_data = webull.deep_search(tlg, 'MDAX')
        assert tlg_data and tlg_data['symbol'] == 'TLG'
        mt = Stock(name='ARCELORMITTAL SA', symbol='MT')
        mt_data = webull.deep_search(mt, 'CAC 40')
        assert mt_data and mt_data['symbol'] == 'ARRD'
        en = Stock(name='Bouygues', symbol='EN')
        en_data = webull.deep_search(en, 'CAC 40')
        assert en_data and en_data['symbol'] == 'BYG'
        rio = Stock(name='Rio Tinto', symbol='RIO')
        rio_data = webull.deep_search(rio, 'FTSE 100')
        assert rio_data and rio_data['symbol'] == 'RIO'
        metr = Stock(name='METRO Wholesale & Food Specialist AG', symbol='B4B')
        metr_data = webull.deep_search(metr, 'MDAX')
        assert metr_data and metr_data['symbol'] == 'B4B'
        axa = Stock(name='AXA', symbol='CS')
        axa_data = webull.deep_search(axa, 'CAC 40')
        assert axa_data and axa_data['symbol'] == 'AXA'
        mmm = Stock(name='3M', symbol='MMM')
        mmm_data = webull.deep_search(mmm, 'S&P 500')
        assert mmm_data and mmm_data['symbol'] == 'MMM'
        # T-Mobile US TMUS
        tmus = Stock(name='T-Mobile US', symbol='TMUS')
        tmus_data = webull.deep_search(tmus, 'S&P 500')
        assert tmus_data and tmus_data['symbol'] == 'TMUS'
        # CME Group Inc CME S&P 500
        cme = Stock(name='CME Group Inc', symbol='CME')
        cme_data = webull.deep_search(cme, 'S&P 500')
        assert cme_data and cme_data['symbol'] == 'CME'
        # Wärtsilä Corporation OMX Helsinki 15:WRT1V to db
        wrt1v = Stock(name='Wärtsilä Corporation', symbol='WRT1V')
        wrt1v_data = webull.deep_search(wrt1v, 'OMX Helsinki 15')
        assert wrt1v_data and wrt1v_data['symbol'] == 'WRT1V'
        # UNIBAIL-WFD UNIBAI CAC 40:URW
        urw = Stock(name='UNIBAIL-WFD UNIBAI', symbol='URW')
        urw_data = webull.deep_search(urw, 'CAC 40')
        assert urw_data and urw_data['name'] == 'UNIBAIL RODAMCO'
        region = webull.get_region(urw_data['tickerId'])
        assert region == 'France'
        # Wüstenrot & Württembergische AG WUW
        wuw = Stock(name='Wüstenrot & Württembergische AG', symbol='WUW')
        wuw_data = webull.deep_search(wuw, 'MDAX')
        assert wuw_data and wuw_data['symbol'] == 'WUW'
        #  ProSiebenSat.1 Media SE PSM:
        pro = Stock(name='ProSiebenSat.1 Media SE', symbol='PSM')
        pro_data = webull.deep_search(pro, 'MDAX')
        assert pro_data and pro_data['symbol'] == 'PSM'
        # FANG Diamondback Energy S&P 500
        fang = Stock(name='Diamondback Energy', symbol='FANG')
        fang_data = webull.deep_search(fang, 'S&P 500')
        assert fang_data and fang_data['symbol'] == 'FANG'
        abmd = Stock(name='ABIOMED', symbol='ABMD')
        symbols = ["ETR:ALV", "ETR:MRK"]
        abmd_data = webull.deep_search(abmd, 'S&P 500')
        assert abmd_data and abmd_data['symbol'] == 'ABMD'
        pm = webull.search_query(['Philip Morris International Inc'], 'PM', ['NYSE'])
        assert pm
        assert pm['name'] == 'PMI'
        ticker_ids = webull.get_ticker_ids(symbols)
        assert len(ticker_ids) == len(symbols)
        for idx, ticker_id in enumerate(ticker_ids):
            TEST_LOGGER.info("%s", symbols[idx])
            TEST_LOGGER.info("Tickerid = %s", ticker_ids[ticker_id])
            TEST_LOGGER.info("Recommendation:")
            js_rec = webull.get_recommendation(ticker_ids[ticker_id])
            TestWebullClient.check_recommendation(js_rec)
            TEST_LOGGER.info(js_rec)
            TEST_LOGGER.info("Income:")
            js_income = webull.get_income(ticker_ids[ticker_id])
            TEST_LOGGER.info(js_income)
            TEST_LOGGER.info("Income sheet:")
            js_income_sheet = webull.get_sheet(ticker_ids[ticker_id], 0)
            TEST_LOGGER.info(js_income_sheet)
            TEST_LOGGER.info("Balance sheet:")
            js_balance_sheet = webull.get_sheet(ticker_ids[ticker_id], 1)
            TEST_LOGGER.info(js_balance_sheet)
            TEST_LOGGER.info("Cash flow sheet:")
            js_cash_sheet = webull.get_sheet(ticker_ids[ticker_id], 2)
            TEST_LOGGER.info(js_cash_sheet)

    @staticmethod
    def test_search():
        """
        test search
        :return:
        """
        webull = Bull(TEST_LOGGER)
        data = webull.search('Dassault Systèmes')
        assert data
        brief = webull.get_company_brief(data['tickerId'])
        assert brief
        region = webull.get_region(data['tickerId'])
        assert region == 'France'

        data = webull.search('Fresenius Medical Care AG & Co KGaA', ['FRA'])
        assert data
        data = webull.search('Henkel AG & Co. KGaA Vz', ['FRA'])
        assert data
        region = webull.get_region(data['tickerId'])
        assert region

if __name__ == '__main__':
    unittest.main()
