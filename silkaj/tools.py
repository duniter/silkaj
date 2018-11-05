from datetime import datetime
from sys import exit

from silkaj.constants import G1_SYMBOL, GTEST_SYMBOL
from silkaj.blockchain_tools import BlockchainParams


def convert_time(timestamp, kind):
    ts = int(timestamp)
    date = "%Y-%m-%d"
    hour = "%H:%M"
    second = ":%S"
    if kind == "all":
        pattern = date + " " + hour + second
    elif kind == "date":
        pattern = date
    elif kind == "hour":
        pattern = hour
        if ts >= 3600:
            pattern += second
    return datetime.fromtimestamp(ts).strftime(pattern)


class CurrencySymbol(object):
    __instance = None

    def __new__(cls):
        if CurrencySymbol.__instance is None:
            CurrencySymbol.__instance = object.__new__(cls)
        return CurrencySymbol.__instance

    def __init__(self):
        currency = BlockchainParams().params["currency"]
        if currency == "g1":
            self.symbol = G1_SYMBOL
        elif currency == "g1-test":
            self.symbol = GTEST_SYMBOL


def message_exit(message):
    print(message)
    exit(1)
