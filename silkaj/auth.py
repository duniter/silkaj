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

from silkaj.crypto_tools import get_publickey_from_seed, b58_decode
from silkaj.tools import message_exit
from nacl import encoding
from getpass import getpass
from os import path
from re import compile, search
from duniterpy.key import SigningKey
from duniterpy.key import ScryptParams


def auth_method(cli_args):
    if cli_args.contains_switches("auth-seed"):
        return auth_by_seed()
    if cli_args.contains_switches("auth-file"):
        return auth_by_auth_file(cli_args)
    if cli_args.contains_switches("auth-wif"):
        return auth_by_wif()
    else:
        return auth_by_scrypt(cli_args)


def generate_auth_file(cli_args):
    if cli_args.contains_definitions("file"):
        file = cli_args.get_definition("file")
    else:
        file = "authfile"
    seed = auth_method(cli_args)
    with open(file, "w") as f:
        f.write(seed)
    print(
        "Authentication file 'authfile' generated and stored in current\
 folder for following public key:",
        get_publickey_from_seed(seed),
    )


def auth_by_auth_file(cli_args):
    if cli_args.contains_definitions("file"):
        file = cli_args.get_definition("file")
    else:
        file = "authfile"
    if not path.isfile(file):
        message_exit('Error: the file "' + file + '" does not exist')
    with open(file) as f:
        filetxt = f.read()

    regex_seed = compile("^[0-9a-fA-F]{64}$")
    regex_gannonce = compile(
        "^pub: [1-9A-HJ-NP-Za-km-z]{43,44}\nsec: [1-9A-HJ-NP-Za-km-z]{88,90}.*$"
    )
    # Seed Format
    if search(regex_seed, filetxt):
        seed = filetxt[0:64]
    # gannonce.duniter.org Format
    elif search(regex_gannonce, filetxt):
        private_key = filetxt.split("sec: ")[1].split("\n")[0]
        seed = encoding.HexEncoder.encode(b58_decode(private_key))[0:64].decode("utf-8")
    else:
        message_exit("Error: the format of the file is invalid")
    return seed


def auth_by_seed():
    seed = input("Please enter your seed on hex format: ")
    regex = compile("^[0-9a-fA-F]{64}$")
    if not search(regex, seed):
        message_exit("Error: the format of the seed is invalid")
    return seed


def auth_by_scrypt(cli_args):
    salt = getpass("Please enter your Scrypt Salt (Secret identifier): ")
    password = getpass("Please enter your Scrypt password (masked): ")

    if (
        cli_args.contains_definitions("n")
        and cli_args.contains_definitions("r")
        and cli_args.contains_definitions("p")
    ):
        n, r, p = (
            cli_args.get_definition("n"),
            cli_args.get_definition("r"),
            cli_args.get_definition("p"),
        )
        if n.isnumeric() and r.isnumeric() and p.isnumeric():
            scrypt_params = ScryptParams(int(n), int(r), int(p))
            if n <= 0 or n > 65536 or r <= 0 or r > 512 or p <= 0 or p > 32:
                message_exit("Error: the values of Scrypt parameters are not good")
        else:
            message_exit("one of n, r or p is not a number")
    else:
        scrypt_params = None
        print("Using default values. Scrypt parameters not specified or wrong format")
        n, r, p = 4096, 16, 1
    print("Scrypt parameters used: N: {0}, r: {1}, p: {2}".format(n, r, p))

    return SigningKey.from_credentials(salt, password, scrypt_params)


def auth_by_wif():
    wif_hex = getpass("Enter your WIF or Encrypted WIF address (masked): ")
    password = getpass(
        "(Leave empty in case WIF format) Enter the Encrypted WIF password (masked): "
    )
    try:
        return SigningKey.from_wif_or_ewif_hex(wif_hex, password)
    except Exception as error:
        message_exit(error)
