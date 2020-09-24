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

# had to import from wot to prevent loop dependencies
from silkaj.wot import display_pubkey_and_checksum
from silkaj.cli import cli
from silkaj.constants import FAILURE_EXIT_STATUS


def test_balance_errors():
    """
    test balance command errors
    """

    # twice the same pubkey
    result = CliRunner().invoke(
        cli,
        [
            "balance",
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
        ],
    )
    pubkeyCk = display_pubkey_and_checksum(
        "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh"
    )
    assert f"ERROR: pubkey {pubkeyCk} was specified many times" in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS

    # wrong pubkey
    result = CliRunner().invoke(
        cli,
        [
            "balance",
            "B",
        ],
    )
    assert "ERROR: pubkey B has a wrong format" in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS

    # no pubkey
    result = CliRunner().invoke(cli, ["balance"])
    assert "You should specify one or many pubkeys" in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS
