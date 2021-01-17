"""
Copyright  2016-2021 Maël Azimi <m.a@moul.re>

Silkaj is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Silkaj is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Silkaj. If not, see <https://www.gnu.org/licenses/>.
"""

from sys import exit
from asyncio import get_event_loop
from functools import update_wrapper

from silkaj.constants import G1_SYMBOL, GTEST_SYMBOL, FAILURE_EXIT_STATUS
from silkaj.blockchain_tools import BlockchainParams


class CurrencySymbol(object):
    __instance = None

    def __new__(cls):
        if CurrencySymbol.__instance is None:
            CurrencySymbol.__instance = object.__new__(cls)
        return CurrencySymbol.__instance

    def __init__(self):
        self.symbol = self.get_symbol()

    async def get_symbol(self):
        params = await BlockchainParams().params
        if params["currency"] == "g1":
            return G1_SYMBOL
        elif params["currency"] == "g1-test":
            return GTEST_SYMBOL


def message_exit(message):
    print(message)
    exit(FAILURE_EXIT_STATUS)


def coroutine(f):
    def wrapper(*args, **kwargs):
        loop = get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return update_wrapper(wrapper, f)
