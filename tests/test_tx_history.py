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
