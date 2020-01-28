# This file contains patched functions for testing purposes.

from silkaj.constants import G1_SYMBOL

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
