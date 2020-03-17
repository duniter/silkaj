## mock head_block()
async def patched_head_block(self):
    mocked_head_block = {
        "number": 48000,
        "unitbase": 0,
        "currency": "g1",
        "hash": "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C",
    }
    return mocked_head_block
