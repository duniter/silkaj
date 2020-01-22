"""
Copyright  2016-2019 Maël Azimi <m.a@moul.re>

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

from silkaj.tools import message_exit
from click import command, option, pass_context, confirm
from getpass import getpass
from pathlib import Path
from re import compile, search, MULTILINE
from duniterpy.key import SigningKey
from duniterpy.key.scrypt_params import ScryptParams


@pass_context
def auth_method(ctx):
    if ctx.obj["AUTH_SEED"]:
        return auth_by_seed()
    if ctx.obj["AUTH_FILE"]:
        return auth_by_auth_file()
    if ctx.obj["AUTH_WIF"]:
        return auth_by_wif()
    else:
        return auth_by_scrypt()


@command("authfile", help="Generate authentication file")
@option("--file", default="authfile", show_default=True, help="Path file")
def generate_auth_file(file):
    key = auth_method()
    authfile = Path(file)
    if authfile.is_file():
        confirm(
            "Would you like to erase "
            + file
            + " by an authfile corresponding to following pubkey `"
            + key.pubkey
            + "`?",
            abort=True,
        )
    key.save_seedhex_file(file)
    print(
        "Authentication file 'authfile' generated and stored in current\
 folder for following public key:",
        key.pubkey,
    )


@pass_context
def auth_by_auth_file(ctx):
    """
    Uses an auth file to generate key.
    Authfile can be either:
    * Seed in hexadecimal encoding
    * PubSec format with public and private key in base58 encoding.
    """
    file = ctx.obj["AUTH_FILE_PATH"]
    authfile = Path(file)
    if not authfile.is_file():
        message_exit('Error: the file "' + file + '" does not exist')
    filetxt = authfile.open("r").read()
    # regex for seed (hexadecimal)
    regex_seed = compile("^[0-9a-fA-F]{64}$")
    # two RE for PubSec format
    regex_pubkey = compile("pub: ([1-9A-HJ-NP-Za-km-z]{43,44})", MULTILINE)
    regex_signkey = compile("sec: ([1-9A-HJ-NP-Za-km-z]{87,90})", MULTILINE)

    # Seed Format
    if search(regex_seed, filetxt):
        return SigningKey.from_seedhex_file(file)
    # PubSec format
    elif search(regex_pubkey, filetxt) and search(regex_signkey, filetxt):
        return SigningKey.from_pubsec_file(file)
    else:
        message_exit("Error: the format of the file is invalid")


def auth_by_seed():
    seedhex = getpass("Please enter your seed on hex format: ")
    try:
        return SigningKey.from_seedhex(seedhex)
    except Exception as error:
        message_exit(error)


@pass_context
def auth_by_scrypt(ctx):
    salt = getpass("Please enter your Scrypt Salt (Secret identifier): ")
    password = getpass("Please enter your Scrypt password (masked): ")

    if ctx.obj["AUTH_SCRYPT_PARAMS"]:
        n, r, p = ctx.obj["AUTH_SCRYPT_PARAMS"].split(",")

        if n.isnumeric() and r.isnumeric() and p.isnumeric():
            n, r, p = int(n), int(r), int(p)
            if n <= 0 or n > 65536 or r <= 0 or r > 512 or p <= 0 or p > 32:
                message_exit("Error: the values of Scrypt parameters are not good")
            scrypt_params = ScryptParams(n, r, p)
        else:
            message_exit("one of n, r or p is not a number")
    else:
        scrypt_params = None

    try:
        return SigningKey.from_credentials(salt, password, scrypt_params)
    except ValueError as error:
        message_exit(error)


def auth_by_wif():
    wif_hex = getpass("Enter your WIF or Encrypted WIF address (masked): ")
    password = getpass(
        "(Leave empty in case WIF format) Enter the Encrypted WIF password (masked): "
    )
    try:
        return SigningKey.from_wif_or_ewif_hex(wif_hex, password)
    except Exception as error:
        message_exit(error)
