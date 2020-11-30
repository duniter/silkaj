# This file contains fake values for testing purposes

from duniterpy.documents.block_uid import BlockUID

currency = "g1"

mocked_block = {
    "number": 48000,
    "time": 1592243760,
    "unitbase": 0,
    "currency": currency,
    "hash": "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C",
}

fake_block_uid = BlockUID(
    48000, "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C"
)


async def patched_params(self):
    return {
        "msValidity": 31557600,
        "msPeriod": 5259600,
    }


async def patched_block(self, number):
    return mocked_block


## mock head_block()
async def patched_head_block(self):
    return mocked_block
