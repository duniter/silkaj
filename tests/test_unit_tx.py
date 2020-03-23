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

import sys
import pytest

from silkaj import tx
from silkaj.tui import display_pubkey, display_amount
from silkaj.constants import (
    G1_SYMBOL,
    CENT_MULT_TO_UNIT,
    MINIMAL_ABSOLUTE_TX_AMOUNT,
)
from silkaj.cli import cli

from click.testing import CliRunner
from click import pass_context

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
from patched.auth import patched_auth_method
from patched.tx import (
    patched_transaction_confirmation,
    patched_handle_intermediaries_transactions,
)

# AsyncMock available from Python 3.8. asynctest is used for Py < 3.8
if sys.version_info[1] > 7:
    from unittest.mock import AsyncMock
else:
    from asynctest.mock import CoroutineMock as AsyncMock

# Values
# fifi: HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat : 53 TX, amount = 5300
key_fifi = patched_auth_method("fifi")


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


# handle_intermediaries_transactions()
@pytest.mark.parametrize(
    "key, issuers, tx_amounts, outputAddresses, Comment, OutputbackChange, expected_listinput_amount",
    [
        # test 1 : with two amounts/outputs and an outputbackchange, no need for intermediary transaction.
        (
            key_fifi,
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            (100, 100),
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            "Test comment",
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            (
                [
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=0,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=1,
                    ),
                ],
                200,
                False,
            ),
        ),
        # test 2 : with one amounts/outputs and no outputbackchange, need for intermediary transaction.
        (
            key_fifi,
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            (4001,),
            [
                "4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw",
            ],
            "Test comment",
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            (
                [
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=0,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=1,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=2,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=3,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=4,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=5,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=6,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=7,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=8,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=9,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=10,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=11,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=12,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=13,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=14,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=15,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=16,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=17,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=18,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=19,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=20,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=21,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=22,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=23,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=24,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=25,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=26,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=27,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=28,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=29,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=30,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=31,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=32,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=33,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=34,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=35,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=36,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=37,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=38,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=39,
                    ),
                ],
                4000,
                True,
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_handle_intermediaries_transactions(
    key,
    issuers,
    tx_amounts,
    outputAddresses,
    Comment,
    OutputbackChange,
    expected_listinput_amount,
    monkeypatch,
):
    # patched functions
    patched_generate_and_send_transaction = AsyncMock(return_value=None)
    monkeypatch.setattr("silkaj.money.get_sources", patched_get_sources)
    monkeypatch.setattr(
        "silkaj.tx.generate_and_send_transaction", patched_generate_and_send_transaction
    )

    patched_get_sources.counter = 0

    # testing
    await tx.handle_intermediaries_transactions(
        key, issuers, tx_amounts, outputAddresses, Comment, OutputbackChange
    )

    if expected_listinput_amount[2] == True:
        patched_generate_and_send_transaction.assert_any_await(
            key,
            issuers,
            [
                expected_listinput_amount[1],
            ],
            expected_listinput_amount,
            [issuers],
            "Change operation",
        )
    else:
        patched_generate_and_send_transaction.assert_awaited_once_with(
            key,
            issuers,
            tx_amounts,
            expected_listinput_amount,
            outputAddresses,
            Comment,
            issuers,
        )


# test send_transaction()
@pytest.mark.parametrize(
    "amounts, amountsud, allsources, recipients, comment, outputbackchange, yes, confirmation_answer",
    [
        (
            [
                2,
            ],
            "",
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "Test",
            None,
            True,
            "",
        ),
        (
            [2],
            "",
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "",
            "",
            False,
            "yes",
        ),
        (
            [2],
            "",
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "Test Comment",
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            False,
            "no",
        ),
        (
            [2],
            "",
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            ],
            "Test Comment",
            None,
            False,
            "yes",
        ),
        (
            [2, 3],
            "",
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            ],
            "Test Comment",
            None,
            False,
            "yes",
        ),
        (
            "",
            [0.5, 1],
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            ],
            "Test Comment",
            None,
            False,
            "yes",
        ),
        (
            "",
            "",
            True,
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "Test Comment",
            None,
            False,
            "yes",
        ),
    ],
)
def test_send_transaction(
    amounts,
    amountsud,
    allsources,
    recipients,
    comment,
    outputbackchange,
    yes,
    confirmation_answer,
    monkeypatch,
):
    """
    This function only tests coherent values.
    Errors are tested in test_tx.py.
    """

    @pass_context
    def patched_auth_method_tx(ctx):
        return key_fifi

    def compute_test_amounts(amounts, mult):
        list_amounts = []
        for amount in amounts:
            list_amounts.append(round(amount * mult))
        return list_amounts

    # construct click arguments list
    def construct_args(
        amounts, amountsud, allsources, recipients, comment, outputbackchange, yes
    ):
        args_list = ["tx"]
        if yes:
            args_list.append("--yes")
        if amounts:
            for amount in amounts:
                args_list.append("-a")
                args_list.append(str(amount))
        elif amountsud:
            for amountud in amountsud:
                args_list.append("-d")
                args_list.append(str(amountud))
        elif allsources:
            args_list.append("--allSources")
        for recipient in recipients:
            args_list.append("-r")
            args_list.append(recipient)
        if comment:
            args_list.append("--comment")
            args_list.append(comment)
        if outputbackchange != None:
            args_list.append("--outputBackChange")
            args_list.append(outputbackchange)
        return args_list

    # mocking functions
    patched_transaction_confirmation = AsyncMock(return_value=None)
    patched_handle_intermediaries_transactions = AsyncMock(return_value=None)

    # patching functions
    monkeypatch.setattr("silkaj.auth.auth_method", patched_auth_method_tx)
    monkeypatch.setattr(
        "silkaj.tx.transaction_confirmation", patched_transaction_confirmation
    )
    monkeypatch.setattr(
        "silkaj.tx.handle_intermediaries_transactions",
        patched_handle_intermediaries_transactions,
    )
    monkeypatch.setattr("silkaj.money.get_sources", patched_get_sources)
    monkeypatch.setattr("silkaj.money.UDValue.get_ud_value", patched_ud_value)

    # reset patched_get_sources
    patched_get_sources.counter = 0
    # total amount for pubkey_fifi
    total_amount = 5300
    # compute amounts list
    if allsources:
        # sum of sources for account "fifi"
        tx_amounts = [total_amount]
    else:
        if amounts:
            mult = CENT_MULT_TO_UNIT
            test_amounts = amounts
        elif amountsud:
            mult = mock_ud_value
            test_amounts = amountsud
        if len(recipients) != len(test_amounts) and len(test_amounts) == 1:
            test_amounts = [test_amounts[0]] * len(recipients)
        tx_amounts = compute_test_amounts(test_amounts, mult)

    # create arguments and run cli
    arguments = construct_args(
        amounts, amountsud, allsources, recipients, comment, outputbackchange, yes
    )
    result = CliRunner().invoke(cli, args=arguments, input=confirmation_answer)
    print(result.output)

    if confirmation_answer:
        patched_transaction_confirmation.assert_any_await(
            key_fifi.pubkey,
            total_amount,
            tx_amounts,
            recipients,
            outputbackchange,
            comment,
        )
    if yes or confirmation_answer == "yes":
        patched_handle_intermediaries_transactions.assert_any_await(
            key_fifi,
            key_fifi.pubkey,
            tx_amounts,
            recipients,
            comment,
            outputbackchange,
        )
    elif confirmation_answer == "no":
        patched_handle_intermediaries_transactions.assert_not_awaited()


# generate_and_send_transaction()


@pytest.mark.parametrize(
    "key, issuers, tx_amounts, listinput_and_amount, outputAddresses, Comment, OutputbackChange, client_return",
    [
        # right tx : 1 amount for 1 receiver
        (
            key_fifi,
            key_fifi.pubkey,
            [
                100,
            ],
            (
                [
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=0,
                    ),
                    InputSource(
                        amount=200,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=1,
                    ),
                    InputSource(
                        amount=300,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=2,
                    ),
                ],
                600,
                False,
            ),
            ("DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",),
            "",
            None,
            True,
        ),
        # right tx : 2 amounts for 2 receivers
        (
            key_fifi,
            key_fifi.pubkey,
            [
                100,
                250,
            ],
            (
                [
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=0,
                    ),
                    InputSource(
                        amount=200,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=1,
                    ),
                    InputSource(
                        amount=300,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=2,
                    ),
                ],
                600,
                False,
            ),
            (
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp",
            ),
            "Test comment",
            None,
            True,
        ),
        # Wrong tx : 3 amounts for 1 receiver
        (
            key_fifi,
            key_fifi.pubkey,
            [
                100,
                150,
                50,
            ],
            (
                [
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=0,
                    ),
                    InputSource(
                        amount=200,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=1,
                    ),
                    InputSource(
                        amount=300,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=2,
                    ),
                ],
                600,
                False,
            ),
            ("DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",),
            "",
            "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            False,
        ),
    ],
)
@pytest.mark.asyncio
async def test_generate_and_send_transaction(
    key,
    issuers,
    tx_amounts,
    listinput_and_amount,
    outputAddresses,
    Comment,
    OutputbackChange,
    client_return,
    monkeypatch,
    capsys,
):

    # create FakeReturn and patched_ClientInstance classes to patch ClientInstance() class
    class FakeReturn:
        def __init__(self):
            self.status = client_return

        async def __call__(self, *args, **kwargs):
            return self

        async def text(self):
            return "Tests for Silkaj : Fake Return !"

    class patched_ClientInstance:
        def __init__(self):
            self.client = FakeReturn()

    # mock functions
    tx.generate_transaction_document = AsyncMock()

    # patched functions
    monkeypatch.setattr(
        "silkaj.blockchain_tools.HeadBlock.get_head", patched_head_block
    )
    monkeypatch.setattr("silkaj.network_tools.ClientInstance", patched_ClientInstance)

    # write the test function
    async def function_testing():
        await tx.generate_and_send_transaction(
            key,
            issuers,
            tx_amounts,
            listinput_and_amount,
            outputAddresses,
            Comment,
            OutputbackChange,
        )
        if client_return != 200:
            assert pytest.raises(SystemExit).type == SystemExit

        display = capsys.readouterr().out
        if listinput_and_amount[2]:
            assert display.find("Generate Change Transaction") != -1
        else:
            assert display.find("Generate Transaction:") != -1
            assert display.find("   - From:    {0}".format(issuers)) != -1
        for tx_amount, outputAddress in zip(tx_amounts, outputAddresses):
            assert display.find(
                "   - To:     {0}\n   - Amount: {1}".format(
                    outputAddress, tx_amount / 100
                )
            )

        tx.generate_transaction_document.assert_awaited_once_with(
            issuers,
            tx_amounts,
            listinput_and_amount,
            outputAddresses,
            Comment,
            OutputbackChange,
        )

        if client_return == 200:
            assert display.find("Transaction successfully sent.") != -1
        else:
            assert display.find("Error while publishing transaction:") != -1

    ### test function and catch SystemExit if needed ###
    if client_return == 200:
        await function_testing()
    else:
        with pytest.raises(SystemExit) as pytest_exit:
            await function_testing()
        assert pytest_exit.type == SystemExit
