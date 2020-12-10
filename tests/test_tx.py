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
from click.testing import CliRunner

from silkaj.tx import transaction_amount
from silkaj.money import UDValue
from silkaj.cli import cli
from silkaj.constants import (
    MINIMAL_ABSOLUTE_TX_AMOUNT,
    MINIMAL_RELATIVE_TX_AMOUNT,
    FAILURE_EXIT_STATUS,
    CENT_MULT_TO_UNIT,
)

from patched.money import patched_ud_value
from patched.test_constants import mock_ud_value


@pytest.mark.asyncio
async def test_transaction_amount(monkeypatch):
    """test passed amounts passed tx command
    float ≠ 100 does not give the exact value"""

    monkeypatch.setattr(UDValue, "get_ud_value", patched_ud_value)
    trials = (
        # tests for --amount (unit)
        ([141.89], None, ["A"], [14189]),
        ([141.99], None, ["A"], [14199]),
        ([141.01], None, ["A"], [14101]),
        ([141.89], None, ["A", "B"], [14189, 14189]),
        ([141.89, 141.99], None, ["A", "B"], [14189, 14199]),
        # tests for --amount_UD
        (None, [1.1], ["A"], [round(1.1 * mock_ud_value)]),
        (
            None,
            [1.9],
            [
                "A",
                "B",
            ],
            [round(1.9 * mock_ud_value), round(1.9 * mock_ud_value)],
        ),
        (None, [1.0001], ["A"], [round(1.0001 * mock_ud_value)]),
        (None, [9.9999], ["A"], [round(9.9999 * mock_ud_value)]),
        (
            None,
            [1.9, 2.3],
            ["A", "B"],
            [round(1.9 * mock_ud_value), round(2.3 * mock_ud_value)],
        ),
    )

    for trial in trials:
        assert trial[3] == await transaction_amount(trial[0], trial[1], trial[2])


# transaction_amount errors()
@pytest.mark.parametrize(
    "amounts, UDs_amounts, outputAddresses, expected",
    [
        (
            None,
            [0.00002],
            ["DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw"],
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
            ["DBM6F5ChMJzpmkUdL5zD9UXKExmZGfQ1AgPDQy4MxSBw"],
            "Error: The number of passed recipients is not the same as the passed amounts.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_transaction_amount_errors(
    amounts, UDs_amounts, outputAddresses, expected, capsys, monkeypatch
):
    # patched functions
    monkeypatch.setattr("silkaj.money.UDValue.get_ud_value", patched_ud_value)

    def too_little_amount(amounts, multiplicator):
        for amount in amounts:
            if amount * multiplicator < MINIMAL_ABSOLUTE_TX_AMOUNT * CENT_MULT_TO_UNIT:
                return True
            return False

    # run tests
    if amounts:
        given_amounts = amounts
    if UDs_amounts:
        given_amounts = UDs_amounts
    # check program exit on error
    with pytest.raises(SystemExit) as pytest_exit:
        # read output to check error.
        await transaction_amount(amounts, UDs_amounts, outputAddresses)
        assert expected == capsys.readouterr()
    assert pytest_exit.type == SystemExit


def test_tx_passed_amount_cli():
    """One option"""
    result = CliRunner().invoke(cli, ["tx", "--amount", "1"])
    assert "Error: Missing option" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "--amountUD", "1"])
    assert "Error: Missing option" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "--allSources"])
    assert "Error: Missing option" in result.output
    assert result.exit_code == 2

    """Multiple options"""
    result = CliRunner().invoke(cli, ["tx", "--amount", 1, "--amountUD", 1])
    assert "Error: Usage" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "--amount", 1, "--allSources"])
    assert "Error: Usage" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "--amountUD", 1, "--allSources"])
    assert "Error: Usage" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(
        cli, ["tx", "--amount", 1, "--amountUD", 1, "--allSources"]
    )
    assert "Error: Usage" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "-r", "A"])
    assert "Error: amount, amountUD or allSources is not set." in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS

    result = CliRunner().invoke(cli, ["tx", "-r", "A", "-r", "B", "--allSources"])
    assert (
        "Error: the --allSources option can only be used with one recipient."
        in result.output
    )
    assert result.exit_code == FAILURE_EXIT_STATUS

    result = CliRunner().invoke(
        cli, ["tx", "-r", "A", "-a", MINIMAL_ABSOLUTE_TX_AMOUNT - 0.001]
    )
    assert "Error: Invalid value for '--amount'" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(
        cli, ["tx", "-r", "A", "-d", MINIMAL_RELATIVE_TX_AMOUNT - 0.0000001]
    )
    assert "Error: Invalid value for '--amountUD'" in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "-r", "A", "-a", 1, "-a", 2])
    assert (
        "Error: The number of passed recipients is not the same as the passed amounts."
        in result.output
    )
    assert result.exit_code == FAILURE_EXIT_STATUS

    result = CliRunner().invoke(
        cli, ["tx", "-r", "A", "-r", "B", "-r", "C", "-a", 1, "-a", 2]
    )
    assert (
        "Error: The number of passed recipients is not the same as the passed amounts."
        in result.output
    )
    assert result.exit_code == FAILURE_EXIT_STATUS
