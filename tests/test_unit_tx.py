import pytest
from silkaj.tx import truncBase, transaction_confirmation
from silkaj.tui import display_pubkey, display_amount
from silkaj.money import UDValue
from silkaj.constants import G1_SYMBOL
import patched

# truncBase()
@pytest.mark.parametrize(
    "amount,base,expected",
    [(0, 0, 0), (10, 2, 0), (100, 2, 100), (306, 2, 300), (3060, 3, 3000)],
)
def test_truncBase(amount, base, expected):
    assert truncBase(amount, base) == expected


# display_amount()
@pytest.mark.parametrize(
    "message, amount, currency_symbol", [("Total", 1000, G1_SYMBOL)]
)
def test_display_amount(message, amount, currency_symbol, monkeypatch):
    ud_value = patched.mock_ud_value
    amount_UD = round(amount / ud_value, 4)
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


# transaction_confirmation()
@pytest.mark.parametrize(
    "issuer_pubkey, pubkey_balance, tx_amount, outputAddresses, outputBackChange, comment, currency_symbol",
    [
        # only one receiver
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            1000,
            ["4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw"],
            "",
            "",
            G1_SYMBOL,
        ],
        # one member receiver
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            1000,
            ["BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh"],
            "",
            "This is a comment",
            G1_SYMBOL,
        ],
        # many receivers and backchange
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            1000,
            [
                "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            "C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH",
            "This is a comment",
            G1_SYMBOL,
        ],
    ],
)
@pytest.mark.asyncio
async def test_transaction_confirmation(
    issuer_pubkey,
    pubkey_balance,
    tx_amount,
    outputAddresses,
    outputBackChange,
    comment,
    currency_symbol,
    monkeypatch,
):
    # patched functions
    monkeypatch.setattr("silkaj.wot.is_member", patched.is_member)
    monkeypatch.setattr("silkaj.money.UDValue.get_ud_value", patched.ud_value)
    monkeypatch.setattr(
        "silkaj.tools.CurrencySymbol.get_symbol", patched.currency_symbol
    )

    # creating expected list
    ud_value = await UDValue().ud_value
    expected = list()
    expected.append(
        [
            "pubkey’s balance before tx",
            str(pubkey_balance / 100) + " " + currency_symbol,
        ]
    )

    display_amount(
        expected,
        "total amount",
        float(tx_amount * len(outputAddresses)),
        ud_value,
        currency_symbol,
    )

    expected.append(
        [
            "pubkey’s balance after tx",
            str(((pubkey_balance - tx_amount * len(outputAddresses)) / 100))
            + " "
            + currency_symbol,
        ]
    )

    await display_pubkey(expected, "from", issuer_pubkey)
    for outputAddress in outputAddresses:
        await display_pubkey(expected, "to", outputAddress)
        display_amount(expected, "amount", tx_amount, ud_value, currency_symbol)
    if outputBackChange:
        await display_pubkey(expected, "Backchange", outputBackChange)

    expected.append(["comment", comment])

    # asserting
    tx = await transaction_confirmation(
        issuer_pubkey,
        pubkey_balance,
        tx_amount,
        outputAddresses,
        outputBackChange,
        comment,
    )
    assert tx == expected
