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

import sys
import pytest

from silkaj import tx, wot, money, tools, blockchain_tools, auth, network_tools
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
    patched_gen_confirmation_table,
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
async def test_gen_confirmation_table(
    issuer_pubkey,
    pubkey_balance,
    tx_amounts,
    outputAddresses,
    outputBackChange,
    comment,
    monkeypatch,
):
    # patched functions
    monkeypatch.setattr(wot, "is_member", patched_is_member)
    monkeypatch.setattr(money.UDValue, "get_ud_value", patched_ud_value)
    monkeypatch.setattr(tools.CurrencySymbol, "get_symbol", patched_currency_symbol)

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
    table_list = await tx.gen_confirmation_table(
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
        assert pytest_exit.type == SystemExit
        expected_error = "Error: amount {0} is too low.\n".format(trial[0][0])
        assert capsys.readouterr().out == expected_error


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
    monkeypatch.setattr(blockchain_tools.HeadBlock, "get_head", patched_head_block)

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
    "pubkey, TXamount, outputs_number, expected",
    [
        # no need for interm tx, around 1 source
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 99, 2, (1, 100, False)),
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 100, 2, (1, 100, False)),
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 101, 2, (2, 200, False)),
        # no need for interm.tx, arbitraty number of sources
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 199, 2, (2, 200, False)),
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 200, 2, (2, 200, False)),
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 201, 2, (3, 300, False)),
        # no need for interm.tx, around last available source
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 299, 2, (3, 300, False)),
        ("CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", 300, 2, (3, 300, False)),
        (
            "CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp",
            301,
            15,
            "Error: you don't have enough money\n",
        ),
        # Same tests with UD sources
        # no need for interm tx, around 1 source
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            mock_ud_value - 1,
            2,
            (1, mock_ud_value, False),
        ),
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            mock_ud_value,
            2,
            (1, mock_ud_value, False),
        ),
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            mock_ud_value + 1,
            2,
            (2, mock_ud_value * 2, False),
        ),
        # no need for interm.tx, arbitraty number of sources
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            5 * mock_ud_value - 1,
            2,
            (5, 5 * mock_ud_value, False),
        ),
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            5 * mock_ud_value,
            2,
            (5, 5 * mock_ud_value, False),
        ),
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            5 * mock_ud_value + 1,
            2,
            (6, 6 * mock_ud_value, False),
        ),
        # no need for interm.tx, around last available source
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            10 * mock_ud_value - 1,
            1,
            (10, 10 * mock_ud_value, False),
        ),
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            10 * mock_ud_value,
            2,
            (10, 10 * mock_ud_value, False),
        ),
        (
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            10 * mock_ud_value + 1,
            1,
            "Error: you don't have enough money\n",
        ),
        # high limit for input number
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4600, 2, (46, 4600, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4601, 2, (46, 4600, True)),
        # many outputs
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 3999, 15, (40, 4000, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4000, 15, (40, 4000, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4001, 15, (41, 4100, True)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4600, 15, (46, 4600, True)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4601, 15, (46, 4600, True)),
        # higher limit for outputs
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 99, 93, (1, 100, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 100, 93, (1, 100, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 101, 93, (2, 200, True)),
        # 1 ouput should rarely occur, but we should test it.
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4599, 1, (46, 4600, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4600, 1, (46, 4600, False)),
        ("HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", 4601, 1, (46, 4600, True)),
        # mix UD and TX source
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 2500, 15, (8, 2512, False)),
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 7800, 15, (25, 7850, False)),
        # need for interm tx
        ("9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", 14444, 15, (46, 14444, True)),
        # 93 outputs, should send 1 input only
        ("BdanxHdwRRzCXZpiqvTVTX4gyyh6qFTYjeCWCkLwDifx", 9100, 91, (1, 9600, False)),
    ],
)
@pytest.mark.asyncio
async def test_get_list_input_for_transaction(
    pubkey, TXamount, outputs_number, expected, monkeypatch, capsys
):
    """
    expected is [len(listinput), amount, IntermediateTransaction] or "Error"
    see patched_get_sources() to compute expected values.
    """

    # patched functions
    monkeypatch.setattr(money, "get_sources", patched_get_sources)
    # reset patched_get_sources counter
    patched_get_sources.counter = 0
    # testing error exit
    if isinstance(expected, str):
        with pytest.raises(SystemExit) as pytest_exit:
            result = await tx.get_list_input_for_transaction(
                pubkey, TXamount, outputs_number
            )
        assert expected == capsys.readouterr().out
        assert pytest_exit.type == SystemExit
    # testing good values
    else:
        result = await tx.get_list_input_for_transaction(
            pubkey, TXamount, outputs_number
        )
        assert (len(result[0]), result[1], result[2]) == expected


# handle_intermediaries_transactions()
@pytest.mark.parametrize(
    "key, issuers, tx_amounts, outputAddresses, Comment, OutputbackChange, expected_listinput_amount",
    [
        # test 1 : with two amounts/outputs and an outputbackchange, no need for intermediary transaction.
        (
            key_fifi,
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            [100] * 2,
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
        # test 2 : with 15 amounts/outputs and no outputbackchange, need for intermediary transaction.
        (
            key_fifi,
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            [350] * 14,  # total 4900, pubkey has 5300
            ["4szFkvQ5tzzhwcfUtZD32hdoG2ZzhvG3ZtfR61yjnxdw"] * 14,
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
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=40,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=41,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=42,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=43,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=44,
                    ),
                    InputSource(
                        amount=100,
                        base=0,
                        source="T",
                        origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                        index=45,
                    ),
                ],
                4600,
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
    monkeypatch.setattr(money, "get_sources", patched_get_sources)
    monkeypatch.setattr(
        tx, "generate_and_send_transaction", patched_generate_and_send_transaction
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
    patched_gen_confirmation_table = AsyncMock(return_value=None)
    patched_handle_intermediaries_transactions = AsyncMock(return_value=None)

    # patching functions
    monkeypatch.setattr(auth, "auth_method", patched_auth_method_tx)
    monkeypatch.setattr(tx, "gen_confirmation_table", patched_gen_confirmation_table)
    monkeypatch.setattr(
        tx,
        "handle_intermediaries_transactions",
        patched_handle_intermediaries_transactions,
    )
    monkeypatch.setattr(money, "get_sources", patched_get_sources)
    monkeypatch.setattr(money.UDValue, "get_ud_value", patched_ud_value)

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
        patched_gen_confirmation_table.assert_any_await(
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
    monkeypatch.setattr(blockchain_tools.HeadBlock, "get_head", patched_head_block)
    monkeypatch.setattr(network_tools, "ClientInstance", patched_ClientInstance)

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


# test check_transaction_values()
@pytest.mark.parametrize(
    # issuer_pubkey can be invalid. It is only used for display.
    "comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey, expected_outputBackchange",
    [
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "",
            False,
            "A",
            "",
        ),
        (
            "",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            ],
            "Hvrm4fZQWQ2M26wNczZcijce7cB8XQno2NPTwf5MovPa:5XP",
            False,
            "A",
            "Hvrm4fZQWQ2M26wNczZcijce7cB8XQno2NPTwf5MovPa",
        ),
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            False,
            "A",
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
        ),
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ]
            * 92,
            "",
            False,
            "A",
            "",
        ),
    ],
)
def test_check_transaction_values(
    comment,
    outputAddresses,
    outputBackChange,
    enough_source,
    issuer_pubkey,
    expected_outputBackchange,
    capsys,
):
    result = tx.check_transaction_values(
        comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey
    )
    assert capsys.readouterr().out == ""
    assert result == expected_outputBackchange


# test check_transaction_values()
@pytest.mark.parametrize(
    # issuer_pubkey can be invalid. It is only used for display.
    "comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey",
    [
        (
            "Wrong_Char_é",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "",
            False,
            "A",
        ),
        (
            "Test",
            [
                "Wrong_Pubkey",
            ],
            "",
            False,
            "A",
        ),
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
                "Wrong_Pubkey",
            ],
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            False,
            "A",
        ),
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "Wrong_Pubkey",
            False,
            "A",
        ),
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            True,
            "A",
        ),
        (
            "a" * 256,
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ],
            "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat",
            False,
            "A",
        ),
        (
            "Test",
            [
                "DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw",
            ]
            * 93,
            "",
            False,
            "A",
        ),
    ],
)
def test_check_transaction_values_errors(
    comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey, capsys
):
    with pytest.raises(SystemExit) as pytest_exit:
        result = tx.check_transaction_values(
            comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey
        )
    assert pytest_exit.type == SystemExit
    display = capsys.readouterr()
    if comment.find("Wrong_Char_") != -1:
        assert display.out == "Error: the format of the comment is invalid\n"
    elif len(comment) > tx.MAX_COMMENT_LENGTH:
        assert display.out == "Error: Comment is too long\n"
    elif "Wrong_Pubkey" in outputAddresses:
        assert display.out.find("Error: bad format for following public key:") != -1
    elif outputBackChange:
        if outputBackChange == "Wrong_Pubkey":
            assert display.out.find("Error: bad format for following public key:") != -1
    elif enough_source is True:
        assert (
            display.out.find("pubkey doesn’t have enough money for this transaction.")
            != -1
        )


# test generate_unlocks()
@pytest.mark.parametrize(
    "listinput, expected",
    [
        (
            [
                InputSource(
                    amount=100,
                    base=0,
                    source="T",
                    origin_id="1F3059ABF35D78DFB5AFFB3DEAB4F76878B04DB6A14757BBD6B600B1C19157E7",
                    index=2,
                ),
                InputSource(
                    amount=mock_ud_value,
                    base=0,
                    source="D",
                    origin_id="2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
                    index=6,
                ),
            ],
            [
                Unlock(index=0, parameters=[SIGParameter(0)]),
                Unlock(index=1, parameters=[SIGParameter(0)]),
            ],
        ),
    ],
)
def test_generate_unlocks(listinput, expected):
    assert expected == tx.generate_unlocks(listinput)


# test generate_output
@pytest.mark.parametrize(
    "listoutput, unitbase, rest, recipient_address, expected",
    [
        (
            [],
            0,
            500,
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            [
                OutputSource(
                    amount="500",
                    base=0,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                )
            ],
        ),
        (
            [],
            2,
            314,
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            [
                OutputSource(
                    amount="3",
                    base=2,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                ),
                OutputSource(
                    amount="1",
                    base=1,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                ),
                OutputSource(
                    amount="4",
                    base=0,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                ),
            ],
        ),
        (
            [
                OutputSource(
                    amount="100",
                    base=0,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                )
            ],
            0,
            500,
            "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY",
            [
                OutputSource(
                    amount="100",
                    base=0,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                ),
                OutputSource(
                    amount="500",
                    base=0,
                    condition="SIG(2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY)",
                ),
            ],
        ),
    ],
)
def test_generate_output(listoutput, unitbase, rest, recipient_address, expected):
    tx.generate_output(listoutput, unitbase, rest, recipient_address)
    assert len(expected) == len(listoutput)
    for e, o in zip(expected, listoutput):
        assert e == o


# test max_inputs_number
@pytest.mark.parametrize(
    "outputs_number, issuers_number, expected",
    [
        (1, 1, 47),
        (2, 1, 46),
        (93, 1, 1),
        (1, 2, 46),
        (2, 2, 45),
        (1, 47, 1),
    ],
)
def test_max_inputs_number(outputs_number, issuers_number, expected):
    """
    returns the maximum number of inputs.
    This function does not take care of backchange line.
    formula is IU <= (MAX_LINES_IN_TX_DOC - FIX_LINES - O - 2*IS)/2
    """
    assert tx.max_inputs_number(outputs_number, issuers_number) == expected
