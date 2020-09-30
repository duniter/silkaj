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

from silkaj.cli import cli
from silkaj.checksum import MESSAGE


pubkey = "3rp7ahDGeXqffBQTnENiXEFXYS7BRjYmS33NbgfCuDc8"
checksum = "DFQ"
pubkey_checksum = pubkey + ":" + checksum
pubkey_seedhex_authfile = (
    "3bc6f2484e441e40562155235cdbd8ce04c25e7df35bf5f87c067bf239db8511"
)


@pytest.mark.parametrize(
    "command, excepted_output",
    [
        (["checksum", pubkey_checksum], "The checksum is valid"),
        (["checksum", pubkey + ":vAK"], "The checksum is invalid"),
        (["checksum", pubkey], pubkey_checksum),
        (["checksum", "uid"], "Error: Wrong public key format"),
        (["checksum"], MESSAGE),
        (["--auth-file", "checksum"], pubkey_checksum),
        (["--auth-file", "checksum", "pubkey"], pubkey_checksum),
    ],
)
def test_checksum_command(command, excepted_output):
    with CliRunner().isolated_filesystem():
        with open("authfile", "w") as f:
            f.write(pubkey_seedhex_authfile)
        result = CliRunner().invoke(cli, args=command)
        assert result.output == excepted_output + "\n"
