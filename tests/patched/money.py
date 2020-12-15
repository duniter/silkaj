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

from silkaj.constants import G1_SYMBOL, SOURCES_PER_TX
from silkaj.money import amount_in_current_base
from duniterpy.documents.transaction import InputSource
from patched.test_constants import mock_ud_value


async def patched_ud_value(self):
    return mock_ud_value


# mock get_sources()
async def patched_get_sources(pubkey):
    """
    Returns transaction sources.
    This function doesn't cover all possibilities : only SIG() unlock condition.

    Can be called many times (depending on pubkey).
    If so, it will mock intermediary tx for the first 40 inputs.
    Tests using this function should reset the counter at the begining of each test case.
    See source_dict.py for inputs lists.

    all UTXO have the same amount : 100
    all UD have the same amount : 314

    for pubkey CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp : 3 TX, balance = 300
    for pubkey HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat : 53 TX, balance = 5300
    for pubkey 2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY : 10 UD, balance = 3140
    for pubkey 9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp : 50 UD and 20 TX, balance = 17700
    else : 0 sources, balance = 0
    Same hash for each TX for convenience. This may change for other testing purposes.
    """

    def listinput_UD(listinput, balance, pubkey, max_ud):
        a = 0
        while a < max_ud:
            listinput.append(
                InputSource(
                    amount=mock_ud_value,
                    base=0,
                    source="D",
                    origin_id=pubkey,
                    index=a,
                )
            )
            balance += amount_in_current_base(listinput[-1])
            a += 1
        return balance

    def listinput_TX(listinput, balance, max_tx):
        a = 0
        while a < max_tx:
            listinput.append(
                InputSource(
                    amount=100,
                    base=0,
                    source="T",
                    origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                    index=a,
                )
            )
            balance += amount_in_current_base(listinput[-1])
            a += 1
        return balance

    listinput, n = list(), 0
    balance = 0
    if pubkey == "CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp":
        max_ud = 0
        max_tx = 3
    elif pubkey == "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat":
        if patched_get_sources.counter == 0:
            max_ud = 0
            max_tx = 53
        elif patched_get_sources.counter == 1:
            listinput.append(
                InputSource(
                    amount=100 * SOURCES_PER_TX,  # 100 * 40 = 4000
                    base=0,
                    source="T",
                    origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                    index=93,
                )
            )
            max_ud = 0
            max_tx = 6
    elif pubkey == "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY":
        max_ud = 10
        max_tx = 0
    elif pubkey == "9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp":
        if patched_get_sources.counter == 0:
            max_ud = 50
            max_tx = 20
        elif patched_get_sources.counter == 1:
            listinput.append(
                InputSource(
                    amount=mock_ud_value * SOURCES_PER_TX,  # 40 UD = 40*314 = 12560
                    base=0,
                    source="T",
                    origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                    index=93,
                )
            )
            max_ud = 4
            max_tx = 20
    else:
        max_ud = 0
        max_tx = 0

    balance = listinput_UD(listinput, balance, pubkey, max_ud)
    balance = listinput_TX(listinput, balance, max_tx)

    patched_get_sources.counter += 1
    return listinput, balance


patched_get_sources.counter = 0
