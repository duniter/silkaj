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
from silkaj.tx_history import (
    get_transactions_history,
    remove_duplicate_txs,
    generate_table,
)
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
    await get_transactions_history(client, pubkey, received_txs, sent_txs)

    remove_duplicate_txs(received_txs, sent_txs)
    txs_list = await generate_table(
        received_txs, sent_txs, pubkey, ud_value, currency, uids
    )
    await client.close()

    for tx_list in txs_list:
        assert len(tx_list) == table_columns
