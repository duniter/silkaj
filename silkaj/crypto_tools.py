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

import re
from nacl import encoding, hash

from silkaj.constants import PUBKEY_PATTERN

PUBKEY_DELIMITED_PATTERN = "^{0}$".format(PUBKEY_PATTERN)
CHECKSUM_PATTERN = "[1-9A-HJ-NP-Za-km-z]{3}"
PUBKEY_CHECKSUM_PATTERN = "^{0}:{1}$".format(PUBKEY_PATTERN, CHECKSUM_PATTERN)


def check_public_key(pubkey, display_error):
    """
    Check public key format
    Check pubkey checksum which could be append after the pubkey
    If check pass: return pubkey
    """
    if re.search(re.compile(PUBKEY_DELIMITED_PATTERN), pubkey):
        return pubkey
    elif re.search(re.compile(PUBKEY_CHECKSUM_PATTERN), pubkey):
        pubkey, checksum = pubkey.split(":")
        checksum_calculed = gen_checksum(pubkey)
        if checksum_calculed == checksum:
            return pubkey
        else:
            print("Error: Wrong checksum for following public key:")
            return False

    elif display_error:
        print("Error: bad format for following public key:", pubkey)
    return False


def gen_checksum(pubkey):
    """
    Returns the checksum of the input pubkey (encoded in b58)
    """
    pubkey_byte = b58_decode(pubkey)
    return b58_encode(
        hash.sha256(hash.sha256(pubkey_byte, encoding.RawEncoder), encoding.RawEncoder)
    )[:3]


b58_digits = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58_encode(b):

    # Convert big-endian bytes to integer
    n = int("0x0" + encoding.HexEncoder.encode(b).decode("utf8"), 16)

    # Divide that integer into base58
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(b58_digits[r])
    res = "".join(res[::-1])

    # Encode leading zeros as base58 zeros
    czero = 0
    pad = 0
    for c in b:
        if c == czero:
            pad += 1
        else:
            break
    return b58_digits[0] * pad + res


def b58_decode(s):
    if not s:
        return b""

    # Convert the string to an integer
    n = 0
    for c in s:
        n *= 58
        if c not in b58_digits:
            raise InvalidBase58Error(
                "Character %r is not a " + "valid base58 character" % c
            )
        digit = b58_digits.index(c)
        n += digit

    # Convert the integer to bytes
    h = "%x" % n
    if len(h) % 2:
        h = "0" + h
    res = encoding.HexEncoder.decode(h.encode("utf8"))

    # Add padding back.
    pad = 0
    for c in s[:-1]:
        if c == b58_digits[0]:
            pad += 1
        else:
            break
    return b"\x00" * pad + res
