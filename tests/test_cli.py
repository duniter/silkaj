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

from click.testing import CliRunner

from silkaj.cli import cli
from silkaj.constants import FAILURE_EXIT_STATUS


def test_cli_dry_run_display_options_passed_together():
    # Run command with dry_run and display options
    command = ["--dry-run", "--display", "membership"]
    result = CliRunner().invoke(cli, args=command)

    error_msg = "ERROR: display and dry-run options can not be used together\n"
    assert error_msg == result.output
    assert result.exit_code == FAILURE_EXIT_STATUS
