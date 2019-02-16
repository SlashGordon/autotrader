from autotrader.indicators.averages import *
from autotrader.indicators.trend import *
from autotrader.indicators.oscillators import *
from autotrader.indicators.volume import *

AVERAGES = [Tmacs, Macs]
TREND = [Ar, Macdh]
OSCILLATORS = [Uoe, So]
INDICATORS = AVERAGES + TREND + OSCILLATORS
