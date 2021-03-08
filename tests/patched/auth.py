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

# This file contains patches for auth functions.

from duniterpy.key import SigningKey


def patched_auth_method(uid):
    """
    insecure way to test keys
    """
    return SigningKey.from_credentials(uid, uid)


def patched_auth_by_seed():
    return "call_auth_by_seed"


def patched_auth_by_wif():
    return "call_auth_by_wif"


def patched_auth_by_auth_file():
    return "call_auth_by_auth_file"


def patched_auth_by_scrypt():
    return "call_auth_by_scrypt"
