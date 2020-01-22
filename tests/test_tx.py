import pytest
from click.testing import CliRunner
from silkaj.tx import transaction_amount
from silkaj.money import UDValue
from silkaj.cli import cli


@pytest.mark.asyncio
async def test_transaction_amount():
    """test passed amounts passed tx command
    float ≠ 100 does not give the exact value"""

    assert await transaction_amount(141.89, None, None) == 14189
    assert await transaction_amount(141.99, None, None) == 14199
    assert await transaction_amount(141.01, None, None) == 14101

    ud_value = await UDValue().ud_value
    assert await transaction_amount(None, 1.1, None) == round(1.1 * ud_value)
    assert await transaction_amount(None, 1.9, None) == round(1.9 * ud_value)
    assert await transaction_amount(None, 1.0001, None) == round(1.0001 * ud_value)
    assert await transaction_amount(None, 9.9999, None) == round(9.9999 * ud_value)


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
