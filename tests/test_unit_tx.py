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
from silkaj.tx import (
    truncBase,
    transaction_confirmation,
    compute_amounts,
    transaction_amount,
    generate_transaction_document,
    get_list_input_for_transaction,
)
from silkaj.tui import display_pubkey, display_amount
from silkaj.money import UDValue
from silkaj.constants import G1_SYMBOL, CENT_MULT_TO_UNIT, MINIMAL_TX_AMOUNT
from duniterpy.documents.transaction import (
    InputSource,
    Transaction,
    OutputSource,
    Unlock,
    SIGParameter,
)
from duniterpy.documents.block_uid import BlockUID

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
def test_display_amount(message, amount, currency_symbol):
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


# transaction_confirmation()
@pytest.mark.parametrize(
    "issuer_pubkey, pubkey_balance, tx_amounts, outputAddresses, outputBackChange, comment, currency_symbol",
    [
        # only one receiver
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            [1000],
            ["4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw"],
            "",
            "",
            G1_SYMBOL,
        ],
        # one member receiver
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            [1000],
            ["BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh"],
            "",
            "This is a comment",
            G1_SYMBOL,
        ],
        # many receivers and backchange
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            [1000, 1000],
            [
                "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            "C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH",
            "This is a comment",
            G1_SYMBOL,
        ],
        # many receivers and outputs
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            [1000, 250],
            [
                "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            "",
            "This is a comment",
            G1_SYMBOL,
        ],
    ],
)
@pytest.mark.asyncio
async def test_transaction_confirmation(
    issuer_pubkey,
    pubkey_balance,
    tx_amounts,
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
    total_tx_amount = sum(tx_amounts)
    # display account situation
    display_amount(
        expected,
        "pubkey's balance before tx",
        pubkey_balance,
        ud_value,
        currency_symbol,
    )
    display_amount(
        expected,
        "total transaction amount",
        total_tx_amount,
        ud_value,
        currency_symbol,
    )
    display_amount(
        expected,
        "pubkey's balance after tx",
        (pubkey_balance - total_tx_amount),
        ud_value,
        currency_symbol,
    )
    await display_pubkey(expected, "from", issuer_pubkey)
    # display recipients and amounts
    for outputAddress, tx_amount in zip(outputAddresses, tx_amounts):
        await display_pubkey(expected, "to", outputAddress)
        display_amount(expected, "amount", tx_amount, ud_value, currency_symbol)
    # display backchange and comment
    if outputBackChange:
        await display_pubkey(expected, "Backchange", outputBackChange)
    expected.append(["comment", comment])

    # asserting
    tx = await transaction_confirmation(
        issuer_pubkey,
        pubkey_balance,
        tx_amounts,
        outputAddresses,
        outputBackChange,
        comment,
    )
    assert tx == expected


# compute_amounts()
def test_compute_amounts_errors(capsys):
    trials = (((0.0031, 1), 314),)
    for trial in trials:
        # check program exit on error
        with pytest.raises(SystemExit) as pytest_exit:
            # read output to check error.
            compute_amounts(
                trial[0],
                trial[1],
            )
            expected_error = "Error: amount {0} is too low.".format(trial[0][0])
            assert capsys.readouterr() == expected_error
        assert pytest_exit.type == SystemExit


def test_compute_amounts():
    ud_value = 314
    assert compute_amounts((10.0, 2.0, 0.01, 0.011, 0.019), 100) == [
        1000,
        200,
        1,
        1,
        2,
    ]
    assert compute_amounts([0.0032], ud_value) == [1]
    assert compute_amounts([1.00], ud_value) == [314]
    assert compute_amounts([1.01], ud_value) == [317]
    assert compute_amounts([1.99], ud_value) == [625]
    assert compute_amounts([1.001], ud_value) == [314]
    assert compute_amounts([1.009], ud_value) == [317]
    # This case will not happen in real use, but this particular function will allow it.

    assert compute_amounts([0.0099], 100) == [1]


# transaction_amount()
@pytest.mark.parametrize(
    "amounts, UDs_amounts, outputAddresses, expected",
    [
        ([10], None, ["DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw"], [1000]),
        (
            [10, 2.37],
            None,
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            [1000, 237],
        ),
        (
            [10],
            None,
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            [1000, 1000],
        ),
        (None, [1.263], ["DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw"], [397]),
        (
            None,
            [0.5, 10],
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            [157, 3140],
        ),
        (
            None,
            [0.5],
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            [157, 157],
        ),
        (
            None,
            [0.00002],
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "Error: amount 0.00002 is too low.",
        ),
        (
            [10, 56],
            None,
            ["DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw"],
            "Error: The number of passed recipients is not the same as the passed amounts.",
        ),
        (
            None,
            [1, 45],
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            "Error: The number of passed recipients is not the same as the passed amounts.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_transaction_amount(
    amounts, UDs_amounts, outputAddresses, expected, capsys, monkeypatch
):
    # patched functions
    monkeypatch.setattr("silkaj.money.UDValue.get_ud_value", patched.ud_value)
    udvalue = patched.mock_ud_value

    def too_little_amount(amounts, multiplicator):
        for amount in amounts:
            if amount * multiplicator < MINIMAL_TX_AMOUNT * CENT_MULT_TO_UNIT:
                return True
            return False

    # run tests
    if amounts:
        given_amounts = amounts
    if UDs_amounts:
        given_amounts = UDs_amounts
    # test errors
    if (
        (len(given_amounts) > 1 and len(outputAddresses) != len(given_amounts))
        or (UDs_amounts and too_little_amount(given_amounts, udvalue))
        or (amounts and too_little_amount(given_amounts, CENT_MULT_TO_UNIT))
    ):
        # check program exit on error
        with pytest.raises(SystemExit) as pytest_exit:
            # read output to check error.
            await transaction_amount(amounts, UDs_amounts, outputAddresses)
            assert expected == capsys.readouterr()
        assert pytest_exit.type == SystemExit
    # test good values
    else:
        assert expected == await transaction_amount(
            amounts, UDs_amounts, outputAddresses
        )


# generate_transaction_document()

# expected results
# result 1 : with two amounts/outputs and an outputbackchange
result1 = Transaction(
    version=10,
    currency="g1",
    blockstamp=BlockUID(
        48000, "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C"
    ),
    locktime=0,
    issuers=["BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh"],
    inputs=[
        InputSource(
            10000,
            0,
            "T",
            "B37D161185A760FD81C3242D73FABD3D01F4BD9EAD98C2842061A75BAD4DFA61",
            1,
        ),
        InputSource(
            257,
            0,
            "T",
            "16F1CF9C9B89BB8C34A945F56073AB3C3ACFD858D5FA420047BA7AED1575D1FE",
            1,
        ),
    ],
    unlocks=[
        Unlock(index=0, parameters=[SIGParameter(0)]),
        Unlock(index=1, parameters=[SIGParameter(0)]),
    ],
    outputs=[
        OutputSource(
            amount=str(1000),
            base=0,
            condition="SIG(DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw)",
        ),
        OutputSource(
            amount=str(4000),
            base=0,
            condition="SIG(4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw)",
        ),
        OutputSource(
            amount=str(5000),
            base=0,
            condition="SIG(BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh)",
        ),
    ],
    comment="Test comment",
    signatures=[],
)


@pytest.mark.parametrize(
    "issuers, tx_amounts, listinput_and_amount, outputAddresses, Comment, OutputbackChange, result",
    [
        # test 1 : with two amounts/outputs and an outputbackchange
        (
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
            (1000, 4000),
            [
                [
                    InputSource(
                        10000,
                        0,
                        "T",
                        "B37D161185A760FD81C3242D73FABD3D01F4BD9EAD98C2842061A75BAD4DFA61",
                        1,
                    ),
                    InputSource(
                        257,
                        0,
                        "T",
                        "16F1CF9C9B89BB8C34A945F56073AB3C3ACFD858D5FA420047BA7AED1575D1FE",
                        1,
                    ),
                ],
                10000,
                False,
            ],
            (
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ),
            "Test comment",
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
            result1,
        )
    ],
)
@pytest.mark.asyncio
async def test_generate_transaction_document(
    issuers,
    tx_amounts,
    listinput_and_amount,
    outputAddresses,
    Comment,
    OutputbackChange,
    result,
    monkeypatch,
):
    # patch Head_block
    monkeypatch.setattr(
        "silkaj.blockchain_tools.HeadBlock.get_head", patched.head_block
    )

    assert result == await generate_transaction_document(
        issuers,
        tx_amounts,
        listinput_and_amount,
        outputAddresses,
        Comment,
        OutputbackChange,
    )


# get_list_input_for_transaction()
@pytest.mark.parametrize(
    "pubkey, TXamount, expected",
    [
        ("DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw", 200, (2, 300, False)),
        ("DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw", 600, (3, 600, False)),
        (
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            800,
            "Error: you don't have enough money",
        ),
        ("4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw", 143100, (40, 82000, True)),
        ("BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh", 200, (1, 314, False)),
        ("BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh", 3140, (10, 3140, False)),
        (
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
            5000,
            "Error: you don't have enough money",
        ),
        ("C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH", 2900, (8, 3600, False)),
        ("C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH", 22500, (25, 22570, False)),
        ("C1oAV9FX2y9iz2sdp7kZBFu3EBNAa6UkrrRG3EwouPeH", 29000, (40, 27280, True)),
    ],
)
@pytest.mark.asyncio
async def test_get_list_input_for_transaction(
    pubkey, TXamount, expected, monkeypatch, capsys
):
    """
    expected is [len(listinput), amount, IntermediateTransaction] or "Error"
    see patched.get_sources() to compute expected values.
    """

    # patched functions
    monkeypatch.setattr("silkaj.money.get_sources", patched.get_sources)
    # testing error exit
    if isinstance(expected, str):
        with pytest.raises(SystemExit) as pytest_exit:
            result = await get_list_input_for_transaction(pubkey, TXamount)
            assert expected == capsys.readouterr()
        assert pytest_exit.type == SystemExit
    # testing good values
    else:
        result = await get_list_input_for_transaction(pubkey, TXamount)
        assert (len(result[0]), result[1], result[2]) == expected
