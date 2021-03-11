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

import re
import hashlib

import base58

from silkaj.constants import PUBKEY_PATTERN
from silkaj.tools import message_exit

PUBKEY_DELIMITED_PATTERN = "^{0}$".format(PUBKEY_PATTERN)
CHECKSUM_SIZE = 3
CHECKSUM_PATTERN = f"[1-9A-HJ-NP-Za-km-z]{{{CHECKSUM_SIZE}}}"
PUBKEY_CHECKSUM_PATTERN = "^{0}:{1}$".format(PUBKEY_PATTERN, CHECKSUM_PATTERN)


def is_pubkey_and_check(pubkey):
    """
    Checks if the given argument contains a pubkey.
    If so, verifies the checksum if needed and returns the pubkey.
    Exits if the checksum is wrong.
    Else, return False
    """
    if re.search(re.compile(PUBKEY_PATTERN), pubkey):
        if check_pubkey_format(pubkey, True):
            return validate_checksum(pubkey)
        return pubkey
    return False


def check_pubkey_format(pubkey, display_error=True):
    """
    Checks if a pubkey has a checksum.
    Exits if the pubkey is invalid.
    """
    if re.search(re.compile(PUBKEY_DELIMITED_PATTERN), pubkey):
        return False
    elif re.search(re.compile(PUBKEY_CHECKSUM_PATTERN), pubkey):
        return True
    elif display_error:
        message_exit("Error: bad format for following public key: " + pubkey)
    return


def validate_checksum(pubkey_checksum):
    """
    Check pubkey checksum after the pubkey, delimited by ":".
    If check pass: return pubkey
    Else: exit.
    """
    pubkey, checksum = pubkey_checksum.split(":")
    if checksum == gen_checksum(pubkey):
        return pubkey
    message_exit(
        "Error: public key '"
        + pubkey
        + "' does not match checksum '"
        + checksum
        + "'.\nPlease verify the public key."
    )


def gen_checksum(pubkey):
    """
    Returns the checksum of the input pubkey (encoded in b58)
    """
    pubkey_byte = base58.b58decode(pubkey)
    hash = hashlib.sha256(hashlib.sha256(pubkey_byte).digest()).digest()
    return base58.b58encode(hash)[:3].decode("utf-8")
