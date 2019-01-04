# -*- coding: utf-8 -*-

import click
from sys import stderr
from silkaj.tx import send_transaction
from silkaj.money import cmd_amount
from silkaj.cert import send_certification
from silkaj.commands import (
    currency_info,
    difficulties,
    set_network_sort_keys,
    network_info,
    argos_info,
    list_issuers,
)
from silkaj.tools import message_exit
from silkaj.network_tools import get_request
from silkaj.wot import received_sent_certifications, id_pubkey_correspondence
from silkaj.auth import generate_auth_file
from silkaj.license import display_license
from silkaj.constants import (
    SILKAJ_VERSION,
    G1_SYMBOL,
    GTEST_SYMBOL,
    G1_DEFAULT_ENDPOINT,
    G1_TEST_DEFAULT_ENDPOINT,
)


@click.group()
@click.version_option(version=SILKAJ_VERSION)
@click.option(
    "--peer",
    "-p",
    help="Default endpoint will reach Ğ1 currency with `https://g1.duniter.org` endpoint.\
 Custom endpoint can be specified with `-p` option followed by <domain>:<port>",
)
@click.option(
    "--gtest", "-gt", is_flag=True, help="ĞTest: `https://g1-test.duniter.org` endpoint"
)
@click.option(
    "--auth-scrypt", is_flag=True, help="Scrypt authentication: default method"
)
@click.option(
    "--scrypt-params",
    "--nrp",
    help="Scrypt parameters seperated by commas: defaults N,r,p: 4096,16,1",
)
@click.option(
    "--auth-file", is_flag=True, help="Authentication file. Defaults to: './authfile'"
)
@click.option("--file", help="Path file specification with '--auth-file'")
@click.option("--auth-seed", is_flag=True, help="Seed authentication")
@click.option("--auth-wif", is_flag=True, help="WIF and EWIF authentication methods")
@click.pass_context
def cli(
    ctx, peer, gtest, auth_scrypt, scrypt_params, auth_file, file, auth_seed, auth_wif
):
    ctx.obj = dict()
    ctx.ensure_object(dict)
    ctx.obj["PEER"] = peer
    ctx.obj["GTEST"] = gtest
    ctx.obj["AUTH_SCRYPT"] = auth_scrypt
    ctx.obj["AUTH_SCRYPT_PARAMS"] = scrypt_params
    ctx.obj["AUTH_FILE"] = auth_file
    ctx.obj["AUTH_FILE_PATH"] = file
    ctx.obj["AUTH_SEED"] = auth_seed
    ctx.obj["AUTH_WIF"] = auth_wif


def manage_cmd():
    cli(obj={})


@cli.command("about", help="Display informations about the programm")
def cliAbout():
    about()


@cli.command("amount", help="Get amount of pubkeys")
@click.option(
    "--pubkeys", "-p", help="pubkeys and/or ids separated with colon: <pubkey:pubkey>"
)
def cliAmount(pubkeys):
    cmd_amount(pubkeys)


@cli.command("argos", help="Display currency information formated for Argos or BitBar")
def cliArgos():
    argos_info()


@cli.command("blocks", help="Display blocks")
@click.option(
    "--nbr",
    "-n",
    required=True,
    type=int,
    help="Number of blocks (`0` for current window size), Details blocks are displayed under n <= 30.",
)
@click.option("--detailed", "-d", is_flag=True, help="This flag force detailed view")
def cliBlocks(nbr, detailed):
    list_issuers(nbr, detailed)


@cli.command("cert", help="Send certification")
@click.argument("id_to_certify")
def cliCert(id_to_certify):
    send_certification(id_to_certify)


@cli.command("diffi", help="List proof-of-work difficulty to generate next block")
def cliDiffi():
    difficulties()


@cli.command(
    "generate_auth_file", help="Generate file to store the seed of the account"
)
@click.option("--file", help="Path file")
def cliGenerateAuthFile(file):
    generate_auth_file(file)


@cli.command("id", help="Get corresponding identity or pubkey from pubkey or identity")
@click.argument("id_pubkey")
def cliId(id_pubkey):
    id_pubkey_correspondence(id_pubkey)


@cli.command("info", help="Display information about currency")
def cliInfo():
    currency_info()


@cli.command("license", help="Display Ğ1 license")
def cliLicense():
    display_license()


@cli.command("net", help="Display network")
@click.option(
    "--discover", "-d", is_flag=True, help="Discover all network (could take a while)"
)
@click.option(
    "--sort",
    "-s",
    help='Sort column names comma-separated (for example "-s block,diffi"), optional. Default sort: block,member,diffi,uid',
)
def cliNetwork(discover, sort):
    network_info(discover, sort)


@cli.command("tx", help="Send transaction")
@click.option("--amount", type=float, help="Quantitative value")
@click.option("--amountUD", type=float, help="Relative value")
@click.option("--allSources", is_flag=True, help="Send all sources")
@click.option(
    "--output",
    help="Pubkey(s)’ recipients + optional checksum: <pubkey>[!checksum]:[<pubkey>[!checksum]]",
)
@click.option("--comment", help="Comment")
@click.option(
    "--outputBackChange",
    help="Pubkey recipient to send the rest of the transaction: <pubkey[!checksum]>",
)
@click.option("--yes", "-y", is_flag=True, help="Assume yes. No prompt confirmation")
def cliTransaction(
    amount, amountud, allsources, output, comment, outputbackchange, yes
):
    send_transaction(
        amount, amountud, allsources, output, comment, outputbackchange, yes
    )


@cli.command("usage", help="Display usage")
def cliUsage():
    usage()


@cli.command("wot", help="Display received and sent certifications of an id")
@click.argument("id")
def cliWot(id):
    received_sent_certifications(id)


def usage():
    message_exit(
        "Silkaj: command line client for Duniter currencies\
    \n\nhelp: --help \
    \nversion: --version \
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
    \n - custom endpoint can be specified with [-p | --peer] option followed by <domain>:<port>\
    \n \
    \nCommands: \
    \n - info: Display information about currency \
    \n \
    \n - amount: Get amount of accounts \
    \n      pubkeys and/or ids separated with colon: <pubkey:pubkey>\
    \n      - authentication: see below section\
    \n \
    \n - tx: Send transaction\
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
    \n - net: Display current network with many information \
    \n      [-d | --discover]     Discover all network (could take a while), optional \
    \n      [-s | --sort]     Sort column names comma-separated (for example \"-s block,diffi\"), optional \
    \n                       Default sort is block,member,diffi,uid \
    \n \
    \n - diffi: list proof-of-work difficulty to generate next block \
    \n \
    \n - blocks: display last n blocks (`0` for current window size) \
    \n      [-n | --nbr] detailed blocks are displayed under n <= 30.\
    \n      To force detailed display, use [-d | --detailed] option\
    \n \
    \n - argos: display currency information formated for Argos or BitBar\
    \n \
    \n - generate_auth_file: Generate file to store the seed of the account\
    \n     - authentication: see below section\
    \n \
    \n - id <pubkey> or <identity>: get corresponding identity or pubkey from pubkey or identity.\
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
