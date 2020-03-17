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


# mock UDValue
mock_ud_value = 314


async def patched_ud_value(self):
    return mock_ud_value


# mock get_sources()
async def patched_get_sources(pubkey):
    """
    Returns transaction sources.
    This function doesn't cover all possibilities : only SIG() unlock condition.
    for pubkey DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw : 3 TX, amount = 600
    for pubkey 4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw : 53 TX, amount = 143100
    for pubkey BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh : 10 UD, amount = 3140
    for pubkey C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH : 50 UD and 20 TX, amount = 36700
    else : 0 sources, amount = 0
    Same hash for each TX for convenience. This may change for other testing purposes.
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
    if pubkey == "CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp":
        max_tx = 3
        max_ud = 0
    elif pubkey == "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat":
        max_tx = 53
        max_ud = 0
    elif pubkey == "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY":
        max_tx = 0
        max_ud = 10
    elif pubkey == "9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp":
        max_tx = 20
        max_ud = 50
    else:
        max_tx = 0
        max_ud = 0

    total = max_tx + max_ud
    listinput_TX(listinput, amount, max_tx, total)
    listinput_UD(listinput, amount, pubkey, max_ud, total)

    return listinput, amount
