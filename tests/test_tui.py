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

import pytest
from silkaj.tui import display_pubkey, display_amount
from silkaj.constants import G1_SYMBOL

import patched

# display_amount()
@pytest.mark.parametrize(
    "message, amount, currency_symbol", [("Total", 1000, G1_SYMBOL)]
)
def test_display_amount(message, amount, currency_symbol, monkeypatch):
    ud_value = patched.mock_ud_value
    amount_UD = round(amount / ud_value, 2)
    expected = [
        [
            message + " (unit|relative)",
            str(amount / 100)
            + " "
            + currency_symbol
            + " | "
            + str(amount_UD)
            + " UD "
            + currency_symbol,
        ]
    ]
    tx = list()
    display_amount(tx, message, amount, ud_value, currency_symbol)
    assert tx == expected


# display_pubkey()
@pytest.mark.parametrize(
    "message, pubkey, id",
    [
        ("From", "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh", "riri"),
        ("To", "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw", ""),
    ],
)
@pytest.mark.asyncio
async def test_display_pubkey(message, pubkey, id, monkeypatch):
    monkeypatch.setattr("silkaj.wot.is_member", patched.is_member)

    expected = [[message + " (pubkey)", pubkey]]
    if id:
        expected.append([message + " (id)", id])
    tx = list()
    await display_pubkey(tx, message, pubkey)
    assert tx == expected
