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

from silkaj import tx
from silkaj.tui import display_pubkey, display_amount
from silkaj.constants import (
    G1_SYMBOL,
    CENT_MULT_TO_UNIT,
    MINIMAL_ABSOLUTE_TX_AMOUNT,
)
from duniterpy.documents.transaction import (
    InputSource,
    Transaction,
    OutputSource,
    Unlock,
    SIGParameter,
)

from patched.wot import patched_is_member
from patched.money import patched_get_sources, patched_ud_value
from patched.test_constants import mock_ud_value
from patched.tools import patched_currency_symbol
from patched.blockchain_tools import patched_head_block, fake_block_uid


# truncBase()
@pytest.mark.parametrize(
    "amount,base,expected",
    [(0, 0, 0), (10, 2, 0), (100, 2, 100), (306, 2, 300), (3060, 3, 3000)],
)
def test_truncBase(amount, base, expected):
    assert tx.truncBase(amount, base) == expected


# transaction_confirmation()
@pytest.mark.parametrize(
    "issuer_pubkey, pubkey_balance, tx_amounts, outputAddresses, outputBackChange, comment",
    [
        # only one receiver
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            [1000],
            ["4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw"],
            "",
            "",
        ],
        # one member receiver
        [
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            3000,
            [1000],
            ["BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh"],
            "",
            "This is a comment",
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
    monkeypatch,
):
    # patched functions
    monkeypatch.setattr("silkaj.wot.is_member", patched_is_member)
    monkeypatch.setattr("silkaj.money.UDValue.get_ud_value", patched_ud_value)
    monkeypatch.setattr(
        "silkaj.tools.CurrencySymbol.get_symbol", patched_currency_symbol
    )

    # creating expected list
    expected = list()
    total_tx_amount = sum(tx_amounts)
    # display account situation
    display_amount(
        expected,
        "Initial balance",
        pubkey_balance,
        mock_ud_value,
        G1_SYMBOL,
    )
    display_amount(
        expected,
        "Total transaction amount",
        total_tx_amount,
        mock_ud_value,
        G1_SYMBOL,
    )
    display_amount(
        expected,
        "Balance after transaction",
        (pubkey_balance - total_tx_amount),
        mock_ud_value,
        G1_SYMBOL,
    )
    await display_pubkey(expected, "From", issuer_pubkey)
    # display recipients and amounts
    for outputAddress, tx_amount in zip(outputAddresses, tx_amounts):
        await display_pubkey(expected, "To", outputAddress)
        display_amount(expected, "Amount", tx_amount, mock_ud_value, G1_SYMBOL)
    # display backchange and comment
    if outputBackChange:
        await display_pubkey(expected, "Backchange", outputBackChange)
    expected.append(["Comment", comment])

    # asserting
    table_list = await tx.transaction_confirmation(
        issuer_pubkey,
        pubkey_balance,
        tx_amounts,
        outputAddresses,
        outputBackChange,
        comment,
    )
    assert table_list == expected


# compute_amounts()
def test_compute_amounts_errors(capsys):
    trials = (((0.0031, 1), 314),)
    for trial in trials:
        # check program exit on error
        with pytest.raises(SystemExit) as pytest_exit:
            # read output to check error.
            tx.compute_amounts(
                trial[0],
                trial[1],
            )
            expected_error = "Error: amount {0} is too low.".format(trial[0][0])
            assert capsys.readouterr() == expected_error
        assert pytest_exit.type == SystemExit


def test_compute_amounts():
    assert tx.compute_amounts((10.0, 2.0, 0.01, 0.011, 0.019), 100) == [
        1000,
        200,
        1,
        1,
        2,
    ]
    assert tx.compute_amounts([0.0032], mock_ud_value) == [1]
    assert tx.compute_amounts([1.00], mock_ud_value) == [314]
    assert tx.compute_amounts([1.01], mock_ud_value) == [317]
    assert tx.compute_amounts([1.99], mock_ud_value) == [625]
    assert tx.compute_amounts([1.001], mock_ud_value) == [314]
    assert tx.compute_amounts([1.009], mock_ud_value) == [317]
    # This case will not happen in real use, but this particular function will allow it.
    assert (
        tx.compute_amounts(
            [0.0099],
            100,
        )
        == [1]
    )


# generate_transaction_document()

# expected results
# result 1 : with two amounts/outputs and an outputbackchange
result1 = Transaction(
    version=10,
    currency="g1",
    blockstamp=fake_block_uid,
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
        "silkaj.blockchain_tools.HeadBlock.get_head", patched_head_block
    )

    assert result == await tx.generate_transaction_document(
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
        # less than 1 source
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 99, (1, 100, False)),
        # exactly one source
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 100, (1, 100, False)),
        # more than 1 source and no interm tx
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 150, (2, 200, False)),
        # all sources
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 300, (3, 300, False)),
        # too high amount
        (
            "CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp",
            301,
            "Error: you don't have enough money",
        ),
        # need for an intermediary tx
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4100, (40, 4000, True)),
        # no need for an intermediary tx, but the function still does it
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4000, (40, 4000, True)),
        # less than 1 UD source
        ("2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY", 200, (1, 314, False)),
        # exactly 1 UD source
        ("2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY", 314, (1, 314, False)),
        # all sources with UD sources
        ("2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY", 3140, (10, 3140, False)),
        # too high amount
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            5000,
            "Error: you don't have enough money",
        ),
        # mix UD and TX source
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 2500, (8, 2512, False)),
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 7800, (25, 7850, False)),
        # need for interm tx
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 12561, (40, 12560, True)),
        # no need for interm tx but the function still does it
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 12247, (40, 12560, True)),
        # exactly 39 sources
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 12246, (39, 12246, False)),
    ],
)
@pytest.mark.asyncio
async def test_get_list_input_for_transaction(
    pubkey, TXamount, expected, monkeypatch, capsys
):
    """
    expected is [len(listinput), amount, IntermediateTransaction] or "Error"
    see patched_get_sources() to compute expected values.
    """

    # patched functions
    monkeypatch.setattr("silkaj.money.get_sources", patched_get_sources)
    # reset patched_get_sources counter
    patched_get_sources.counter = 0
    # testing error exit
    if isinstance(expected, str):
        with pytest.raises(SystemExit) as pytest_exit:
            result = await tx.get_list_input_for_transaction(pubkey, TXamount)
            assert expected == capsys.readouterr()
        assert pytest_exit.type == SystemExit
    # testing good values
    else:
        result = await tx.get_list_input_for_transaction(pubkey, TXamount)
        assert (len(result[0]), result[1], result[2]) == expected
