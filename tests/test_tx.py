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
from silkaj.constants import MINIMAL_TX_AMOUNT, FAILURE_EXIT_STATUS
import patched


@pytest.mark.asyncio
async def test_transaction_amount(monkeypatch):
    """test passed amounts passed tx command
    float ≠ 100 does not give the exact value"""

    monkeypatch.setattr(UDValue, "get_ud_value", patched.ud_value)
    udvalue = patched.mock_ud_value
    trials = (
        # tests for --amount (unit)
        ([141.89], None, ["A"], [14189]),
        ([141.99], None, ["A"], [14199]),
        ([141.01], None, ["A"], [14101]),
        ([141.89], None, ["A", "B"], [14189, 14189]),
        ([141.89, 141.99], None, ["A", "B"], [14189, 14199]),
        # tests for --amount_UD
        (None, [1.1], ["A"], [round(1.1 * udvalue)]),
        (
            None,
            [1.9],
            [
                "A",
                "B",
            ],
            [round(1.9 * udvalue), round(1.9 * udvalue)],
        ),
        (None, [1.0001], ["A"], [round(1.0001 * udvalue)]),
        (None, [9.9999], ["A"], [round(9.9999 * udvalue)]),
        (None, [1.9, 2.3], ["A", "B"], [round(1.9 * udvalue), round(2.3 * udvalue)]),
    )

    for trial in trials:
        assert trial[3] == await transaction_amount(trial[0], trial[1], trial[2])


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

    result = CliRunner().invoke(cli, ["tx", "-r", "A", "-a", MINIMAL_TX_AMOUNT - 0.001])
    assert "Error: Invalid value for '--amount'" in result.output
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
