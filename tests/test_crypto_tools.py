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

from silkaj import crypto_tools

# test gen_checksum
@pytest.mark.parametrize(
    "pubkey, checksum",
    [
        ("J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX", "KAv"),
    ],
)
def test_gen_checksum(pubkey, checksum):
    assert checksum == crypto_tools.gen_checksum(pubkey)


# test validate_checksum
@pytest.mark.parametrize(
    "pubkey, checksum,  expected",
    [
        ("J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX", "KAv", None),
        (
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX",
            "KA",
            "Error: Wrong checksum for following public key: J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX",
        ),
    ],
)
def test_validate_checksum(pubkey, checksum, expected, capsys):
    pubkey_with_ck = str(pubkey + ":" + checksum)
    if expected == None:
        assert pubkey == crypto_tools.validate_checksum(pubkey_with_ck)
    else:
        with pytest.raises(SystemExit) as pytest_exit:
            test = crypto_tools.validate_checksum(pubkey_with_ck)
            assert capsys.readouterr() == expected
        assert pytest_exit.type == SystemExit


# test check_pubkey_format
@pytest.mark.parametrize(
    "pubkey, display_error, expected",
    [
        ("J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX:KAv", True, True),
        ("J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX", True, False),
        ("Youpi", False, None),
        ("Youpi", True, "Error: bad format for following public key: Youpi"),
    ],
)
def test_check_pubkey_format(pubkey, display_error, expected, capsys):
    if isinstance(expected, str):
        with pytest.raises(SystemExit) as pytest_exit:
            test = crypto_tools.check_pubkey_format(pubkey, display_error)
            assert capsys.readouterr() == expected
        assert pytest_exit.type == SystemExit
    else:
        assert expected == crypto_tools.check_pubkey_format(pubkey, display_error)


# test is_pubkey_and_check
@pytest.mark.parametrize(
    "uid_pubkey, expected",
    [
        (
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX:KAv",
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX",
        ),
        (
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX",
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX",
        ),
        ("Youpi", False),
    ],
)
def test_is_pubkey_and_check(uid_pubkey, expected):
    assert expected == crypto_tools.is_pubkey_and_check(uid_pubkey)


# test is_pubkey_and_check errors
@pytest.mark.parametrize(
    "uid_pubkey, expected",
    [
        (
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX:KA",
            "Error: bad format for following public key: J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX:KA",
        ),
        (
            "J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX:KAt",
            "Error: Wrong checksum for following public key: J4c8CARmP9vAFNGtHRuzx14zvxojyRWHW2darguVqjtX",
        ),
    ],
)
def test_is_pubkey_and_check_errors(uid_pubkey, expected, capsys):
    with pytest.raises(SystemExit) as pytest_exit:
        test = crypto_tools.is_pubkey_and_check(uid_pubkey)
        assert capsys.readouterr() == expected
    assert pytest_exit.type == SystemExit
