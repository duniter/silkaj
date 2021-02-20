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

import pytest

from silkaj import tx_history, wot
from silkaj.constants import G1_DEFAULT_ENDPOINT, SHORT_PUBKEY_SIZE
from silkaj.crypto_tools import CHECKSUM_SIZE

from patched.tx_history import patched_get_transactions_history
from patched.wot import patched_identities_from_pubkeys
from patched.blockchain_tools import currency

SHORT_PUBKEY_LENGTH_WITH_CHECKSUM = (
    SHORT_PUBKEY_SIZE + CHECKSUM_SIZE + 2
)  # 2 chars "…:" ==> 8 + 3 + 2 = 13


@pytest.mark.asyncio
async def test_tx_history_generate_table(monkeypatch):
    def min_pubkey_length_with_uid(pubkey):
        # uid is at least one char : "<uid> - <pubkey>" adds min 4 chars to <pubkey>
        return pubkey + 4

    monkeypatch.setattr(wot, "identities_from_pubkeys", patched_identities_from_pubkeys)

    client = "whatever"
    ud_value = 10.07
    table_columns = 5
    pubkey = "d88fPFbDdJXJANHH7hedFMaRyGcnVZj9c5cDaE76LRN"

    received_txs, sent_txs = list(), list()
    await patched_get_transactions_history(client, pubkey, received_txs, sent_txs)

    txs_list = await tx_history.generate_table(
        received_txs,
        sent_txs,
        pubkey,
        ud_value,
        currency,
        uids=False,
    )
    for tx_list in txs_list:
        assert len(tx_list) == table_columns
        if tx_list != txs_list[0]:
            assert "…:" in tx_list[1]
            assert len(tx_list[1]) == SHORT_PUBKEY_LENGTH_WITH_CHECKSUM

    txs_list_uids = await tx_history.generate_table(
        received_txs,
        sent_txs,
        pubkey,
        ud_value,
        currency,
        uids=True,
    )
    for tx_list in txs_list_uids:
        assert len(tx_list) == table_columns
        if tx_list != txs_list[0]:
            assert "…:" in tx_list[1]
    # check all lines
    assert len(txs_list_uids[1][1]) >= min_pubkey_length_with_uid(
        SHORT_PUBKEY_LENGTH_WITH_CHECKSUM
    )
    assert len(txs_list_uids[2][1]) == SHORT_PUBKEY_LENGTH_WITH_CHECKSUM
    assert len(txs_list_uids[3][1]) >= min_pubkey_length_with_uid(
        SHORT_PUBKEY_LENGTH_WITH_CHECKSUM
    )
    assert len(txs_list_uids[4][1]) == SHORT_PUBKEY_LENGTH_WITH_CHECKSUM


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
