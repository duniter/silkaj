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

# -*- coding: utf-8 -*-

from click import group, help_option, version_option, option, pass_context

from silkaj.tx import send_transaction
from silkaj.money import cmd_amount
from silkaj.cert import send_certification
from silkaj.commands import (
    currency_info,
    difficulties,
    network_info,
    argos_info,
    list_blocks,
)
from silkaj.tools import message_exit
from silkaj.wot import received_sent_certifications, id_pubkey_correspondence
from silkaj.auth import generate_auth_file
from silkaj.license import license_command
from silkaj.constants import SILKAJ_VERSION


@group()
@help_option("-h", "--help")
@version_option(SILKAJ_VERSION, "-v", "--version")
@option(
    "--peer",
    "-p",
    help="Default endpoint will reach Ğ1 currency with `https://g1.duniter.org` endpoint.\
 Custom endpoint can be specified with `-p` option followed by <domain>:<port>",
)
@option(
    "--gtest", "-gt", is_flag=True, help="ĞTest: `https://g1-test.duniter.org` endpoint"
)
@option(
    "--auth-scrypt",
    "--scrypt",
    is_flag=True,
    help="Scrypt authentication: default method",
)
@option("--nrp", help='Scrypt parameters: defaults N,r,p: "4096,16,1"')
@option(
    "--auth-file",
    "-af",
    is_flag=True,
    help="Authentication file. Defaults to: './authfile'",
)
@option(
    "--file",
    default="authfile",
    show_default=True,
    help="Path file specification with '--auth-file'",
)
@option("--auth-seed", "--seed", is_flag=True, help="Seed hexadecimal authentication")
@option("--auth-wif", "--wif", is_flag=True, help="WIF and EWIF authentication methods")
@pass_context
def cli(ctx, peer, gtest, auth_scrypt, nrp, auth_file, file, auth_seed, auth_wif):
    ctx.obj = dict()
    ctx.ensure_object(dict)
    ctx.obj["PEER"] = peer
    ctx.obj["GTEST"] = gtest
    ctx.obj["AUTH_SCRYPT"] = auth_scrypt
    ctx.obj["AUTH_SCRYPT_PARAMS"] = nrp
    ctx.obj["AUTH_FILE"] = auth_file
    ctx.obj["AUTH_FILE_PATH"] = file
    ctx.obj["AUTH_SEED"] = auth_seed
    ctx.obj["AUTH_WIF"] = auth_wif


cli.add_command(argos_info)
cli.add_command(generate_auth_file)
cli.add_command(cmd_amount)
cli.add_command(list_blocks)
cli.add_command(send_certification)
cli.add_command(difficulties)
cli.add_command(id_pubkey_correspondence)
cli.add_command(currency_info)
cli.add_command(license_command)
cli.add_command(network_info)
cli.add_command(send_transaction)
cli.add_command(received_sent_certifications)


def usage():
    message_exit(
        "Silkaj: command line client for Duniter currencies\
    \n\nhelp: -h, --help, --usage \
    \nversion: -v, --version \
    \nabout: display informations about the programm\
    \n \
    \nEndpoint:\
    \nDefault endpoint will reach "
        + G1_SYMBOL
        + " currency with `https://"
        + G1_DEFAULT_ENDPOINT[0]
        + "` endpoint.\
    \nUse one of these options at the end of the command:\
    \n - `--gtest` to reach "
        + GTEST_SYMBOL
        + " currency with `https://"
        + G1_TEST_DEFAULT_ENDPOINT[0]
        + "` endpoint\
    \n - custom endpoint can be specified with `-p` option followed by <domain>:<port> or <domain> with 443 as default port\
    \n \
    \nCommands: \
    \n - info: Display information about currency \
    \n \
    \n - amount: Get amount of accounts \
    \n      pubkeys and/or ids separated with colon: <pubkey:id:pubkey>\
    \n      - authentication: see below section\
    \n \
    \n - tx/transaction: Send transaction\
    \n     - authentication: see below section\
    \n     - amount:\
    \n         --amountUD=<relative value> | --amount=<quantitative value>\
    \n         [--allSources] \
    \n     --output=<public key>[!checksum]:[<public key>[!checksum]] \
    \n     [--comment=<comment>] \
    \n     [--outputBackChange=<public key[!checksum]>] \
    \n     [-y | --yes], don't ask for prompt confirmation \
    \n \
    \n - cert: Send certification\
    \n     - e.g.: silkaj cert <id> <auth>\
    \n     - authentication: see below section\
    \n \
    \n - net/network: Display current network with many information \
    \n      [--discover]     Discover all network (could take a while), optional \
    \n      [-s | --sort]     Sort column names comma-separated (for example \"-s block,diffi\"), optional \
    \n                       Default sort is block,member,diffi,uid \
    \n \
    \n - diffi: list proof-of-work difficulty to generate next block \
    \n \
    \n - blocks n: display last n blocks (`0` for current window size) \
    \n      last blocks are displayed under n <= 30.\
    \n      To force display last ones, use `--last` option\
    \n \
    \n - argos: display currency information formated for Argos or BitBar\
    \n \
    \n - generate_auth_file: Generate file to store the seed of the account\
    \n     - authentication: see below section\
    \n \
    \n - id/identities <pubkey> or <identity>: get corresponding identity or pubkey from pubkey or identity.\
    \n      it could autocomplete the pubkey corresponding to an identity with three or four following characters.\
    \n \
    \n - wot <pubkey> or <identity>: display received and sent certifications for an account.\
    \n \
    \n - license: display Ğ1 currency license.\
    \n \
    \nAuthentication:\
    \n for amount, transaction, certification, and generate_auth_file commands\
    \n - Scrypt is the default authentication method with 4096,16,1 as default values\
    \n    you can specify others values specifying following parameters: -n <N> -r <r> -p <p>\
    \n - Seed: --auth-seed\
    \n - File: --auth-file [--file=<path file>], './authfile' will be taken if there is no path specified\
    \n - WIF: --auth-wif"
    )


@cli.command("about", help="Display programm information")
def about():
    print(
        "\
\n             @@@@@@@@@@@@@\
\n         @@@     @         @@@\
\n      @@@   @@       @@@@@@   @@.            Silkaj",
        SILKAJ_VERSION,
        "\
\n     @@  @@@       @@@@@@@@@@@  @@,\
\n   @@  @@@       &@@@@@@@@@@@@@  @@@         Powerfull and lightweight command line client\
\n  @@  @@@       @@@@@@@@@#   @@@@ @@(\
\n  @@ @@@@      @@@@@@@@@      @@@  @@        Built in Python for Duniter’s currencies: Ğ1 and Ğ1-Test\
\n @@  @@@      @@@@@@@@ @       @@@  @@\
\n @@  @@@      @@@@@@ @@@@       @@  @@       Authors: moul, tortue, jytou, cebash, cgeek\
\n @@  @@@@      @@@ @@@@@@@      @@  @@\
\n  @@ @@@@*       @@@@@@@@@      @# @@        Website: https://silkaj.duniter.org\
\n  @@  @@@@@    @@@@@@@@@@       @ ,@@\
\n   @@  @@@@@ @@@@@@@@@@        @ ,@@         Repository: https://git.duniter.org/clients/python/silkaj\
\n    @@@  @@@@@@@@@@@@        @  @@*\
\n      @@@  @@@@@@@@        @  @@@            License: GNU AGPLv3\
\n        @@@@   @@          @@@,\
\n            @@@@@@@@@@@@@@@\n",
    )
