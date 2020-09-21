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

from subprocess import check_output

silkaj = ["poetry", "run", "silkaj"]


def test_info():
    """tests 'silkaj info' returns a number of members"""

    output = check_output(silkaj + ["info"])
    assert "Number of members" in output.decode()


def test_wot():
    """tests 'silkaj wot' returns a number of members"""

    output = check_output(silkaj + ["wot", "moul"]).decode()
    assert "moul (GfKERHnJ…:J1k) from block #0-E3B0C44298FC1…" in output
    assert "received_expire" in output
    assert "received" in output
    assert "sent" in output
    assert "sent_expire" in output


def test_id():
    """tests 'silkaj id' certification on gtest"""

    output = check_output(silkaj + ["--gtest", "id", "elois"]).decode()
    assert "D7CYHJXjaH4j7zRdWngUbsURPnSnjsCYtvo6f8dvW3C" in output


def test_balance():
    """tests 'silkaj amount' command on gtest"""

    output = check_output(
        silkaj + ["--gtest", "balance", "3dnbnYY9i2bHMQUGyFp5GVvJ2wBkVpus31cDJA5cfRpj"]
    ).decode()
    assert (
        "│ Balance of pubkey            │ 3dnbnYY9i2bHMQUGyFp5GVvJ2wBkVpus31cDJA5cfRpj:EyF │"
        in output
    )
    assert "│ Total amount (unit|relative) │" in output
    assert "UD ĞTest" in output
    assert "Total relative to M/N" in output
