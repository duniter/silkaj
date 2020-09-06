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
from duniterpy.api.client import Client

from silkaj import tx_history
from silkaj.constants import G1_DEFAULT_ENDPOINT


@pytest.mark.asyncio
async def test_tx_history_generate_table():
    client = Client("BMAS " + " ".join(G1_DEFAULT_ENDPOINT))
    ud_value = 10.07
    currency = "gtest"
    uids = False
    table_columns = 5
    pubkey = "78ZwwgpgdH5uLZLbThUQH7LKwPgjMunYfLiCfUCySkM8"

    received_txs, sent_txs = list(), list()
    await tx_history.get_transactions_history(client, pubkey, received_txs, sent_txs)

    tx_history.remove_duplicate_txs(received_txs, sent_txs)
    txs_list = await tx_history.generate_table(
        received_txs, sent_txs, pubkey, ud_value, currency, uids
    )
    await client.close()

    for tx_list in txs_list:
        assert len(tx_list) == table_columns


@pytest.mark.parametrize(
    "tx_addresses, outputs, occurence, return_value",
    [
        (None, None, 0, ""),
        (None, None, 1, "\n"),
        (None, ["output1"], 0, ""),
        (None, ["output1"], 1, ""),
        (None, ["output1", "output2"], 0, "\n"),
        (None, ["output1", "output2"], 1, "\n"),
        ("pubkey", None, 0, ""),
        ("pubkey", None, 1, "\n"),
        ("pubkey", ["output1"], 0, ""),
        ("pubkey", ["output1"], 1, ""),
        ("Total", ["output1", "output2"], 0, "\n"),
        ("pubkey", ["output1", "output2"], 0, "\n"),
        ("pubkey", ["output1", "output2"], 1, "\n"),
    ],
)
def test_prefix(tx_addresses, outputs, occurence, return_value):
    assert tx_history.prefix(tx_addresses, outputs, occurence) == return_value
