import pytest
from click.testing import CliRunner
from silkaj.tx import transaction_amount
from silkaj.money import UDValue
from silkaj.cli import cli
from silkaj.constants import MINIMAL_TX_AMOUNT


@pytest.mark.asyncio
async def test_transaction_amount():
    """test passed amounts passed tx command
    float ≠ 100 does not give the exact value"""

    udvalue = await UDValue().ud_value
    trials = (
        # tests for --amount (unit)
        ([141.89], None, ["A"], [14189]),
        ([141.99], None, ["A"], [14199]),
        ([141.01], None, ["A"], [14101]),
        ([141.89], None, ["A", "B"], [14189, 14189]),
        ([141.89, 141.99], None, ["A", "B"], [14189, 14199]),
        # tests for --amount_UD
        (None, [1.1], ["A"], [round(1.1 * udvalue)]),
        (None, [1.9], ["A", "B",], [round(1.9 * udvalue), round(1.9 * udvalue)]),
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
    assert result.exit_code == 1

    result = CliRunner().invoke(cli, ["tx", "-r", "A", "-r", "B", "--allSources"])
    assert (
        "Error: the --allSources option can only be used with one recipient."
        in result.output
    )
    assert result.exit_code == 1

    result = CliRunner().invoke(cli, ["tx", "-r", "A", "-a", MINIMAL_TX_AMOUNT - 0.001])
    assert 'Error: Invalid value for "--amount"' in result.output
    assert result.exit_code == 2

    result = CliRunner().invoke(cli, ["tx", "-r", "A", "-a", 1, "-a", 2])
    assert (
        "Error: The number of passed recipients is not the same as the passed amounts."
        in result.output
    )
    assert result.exit_code == 1

    result = CliRunner().invoke(
        cli, ["tx", "-r", "A", "-r", "B", "-r", "C", "-a", 1, "-a", 2]
    )
    assert (
        "Error: The number of passed recipients is not the same as the passed amounts."
        in result.output
    )
    assert result.exit_code == 1
