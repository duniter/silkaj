"""
Copyright  2016-2020 Maël Azimi <m.a@moul.re>

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

# This file contains patched functions for testing purposes.

from silkaj.constants import G1_SYMBOL
from silkaj.money import amount_in_current_base
from duniterpy.documents.transaction import InputSource

## Mocked values

mock_ud_value = 314

pubkey_list = [
    {"pubkey": "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw", "uid": ""},
    {"pubkey": "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw", "uid": ""},
    {"pubkey": "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh", "uid": "riri"},
    {"pubkey": "C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH", "uid": "fifi"},
    {"pubkey": "7Hr6oUxE6nGZxFG7gVbpMK6oUkNTh5eU686EiCXWCrBF", "uid": "loulou"},
]

#### Patched functions ####

## testing tx.py ##

# mock UDValue
async def ud_value(self):
    return mock_ud_value


# mock is_member
async def is_member(pubkey):
    for account in pubkey_list:
        if account["pubkey"] == pubkey:
            if account["uid"]:
                return account
    return False


# mock CurrencySymbol().symbol
async def currency_symbol(self):
    return G1_SYMBOL


## mock head_block()
async def head_block(self):
    mocked_head_block = {
        "number": 48000,
        "unitbase": 0,
        "currency": "g1",
        "hash": "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C",
    }
    return mocked_head_block


# mock get_sources()
async def get_sources(pubkey):
    """
    Returns transaction sources.
    This function does not cover all possibilities : no other unlock conditions than SIG(pubkey).
    if pubkey == DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw : 3 TXsources, amount = 600
    if pubkey == 4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw : 53 TXsources, amount = 143100
    if pubkey == BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh : 10 UDsources, amount = 3140
    if pubkey == C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH : 50 UDsources and 20 TXsources, amount = 36700
    else : 0 sources, amount = 0
    For convenience, the hash is always the same. This should change for other testing purposes.
    """

    def listinput_UD(listinput, amount, pubkey, max_ud, total):
        while max_ud > 0 and total > 0:
            listinput.append(
                InputSource(
                    amount=mock_ud_value,
                    base=0,
                    source="D",
                    origin_id=pubkey,
                    index=max_ud,
                )
            )
            amount += amount_in_current_base(listinput[-1])
            max_ud -= 1
            total -= 1

    def listinput_TX(listinput, amount, max_tx, total):
        orig_max = max_tx + 1
        while max_tx > 0 and total > 0:
            listinput.append(
                InputSource(
                    amount=(orig_max - max_tx) * 100,
                    base=0,
                    source="T",
                    origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                    index=max_tx,
                )
            )
            amount += amount_in_current_base(listinput[-1])
            max_tx -= 1
            total -= 1

    listinput, n = list(), 0
    amount = 0
    if pubkey == "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw":
        max_tx = 3
        max_ud = 0
    elif pubkey == "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw":
        max_tx = 53
        max_ud = 0
    elif pubkey == "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh":
        max_tx = 0
        max_ud = 10
    elif pubkey == "C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH":
        max_tx = 20
        max_ud = 50
    else:
        max_tx = 0
        max_ud = 0

    total = max_tx + max_ud
    listinput_TX(listinput, amount, max_tx, total)
    listinput_UD(listinput, amount, pubkey, max_ud, total)

    return listinput, amount
