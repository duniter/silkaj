# -*- coding: utf-8 -*-

from sys import stderr
from commandlines import Command
from silkaj.tx import send_transaction
from silkaj.money import cmd_amount
from silkaj.cert import send_certification
from silkaj.commands import currency_info, difficulties, set_network_sort_keys,\
        network_info, argos_info, list_issuers
from silkaj.tools import message_exit
from silkaj.network_tools import get_request, get_current_block
from silkaj.wot import received_sent_certifications, id_pubkey_correspondence
from silkaj.auth import generate_auth_file
from silkaj.license import display_license
from silkaj.constants import SILKAJ_VERSION, G1_SYMBOL, GTEST_SYMBOL, G1_DEFAULT_ENDPOINT, G1_TEST_DEFAULT_ENDPOINT


def usage():
    message_exit("Silkaj: command line client for Duniter currencies\
    \n\nhelp: -h, --help, --usage \
    \nversion: -v, --version \
    \nabout: display informations about the programm\
    \n \
    \nEndpoint:\
    \nDefault endpoint will reach " + G1_SYMBOL + " currency with `https://" + G1_DEFAULT_ENDPOINT[0] + "` endpoint.\
    \nUse one of these options at the end of the command:\
    \n - `--gtest` to reach " + GTEST_SYMBOL + " currency with `https://" + G1_TEST_DEFAULT_ENDPOINT[0] + "` endpoint\
    \n - custom endpoint can be specified with `-p` option followed by <domain>:<port>\
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
    \n - issuers n: display last n issuers (`0` for current window size) \
    \n      last issuers are displayed under n <= 30.\
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
    \n - WIF: --auth-wif")


def cli():
    # ep: endpoint, node's network interface
    ep, cli_args = dict(), Command()
    subcmd = ["license", "about", "info", "diffi", "net", "network", "issuers", "argos", "amount", "tx", "transaction", "cert", "generate_auth_file", "id", "identities", "wot"]
    if cli_args.is_version_request():
        message_exit(SILKAJ_VERSION)
    if cli_args.is_help_request() or cli_args.is_usage_request() or cli_args.subcmd not in subcmd:
        usage()
    ep["domain"], ep["port"] = G1_TEST_DEFAULT_ENDPOINT if cli_args.contains_switches("gtest") else G1_DEFAULT_ENDPOINT
    try:
        ep["domain"], ep["port"] = cli_args.get_definition('p').rsplit(':', 1)
    except:
        print("Requested default node: <{}:{}>".format(ep["domain"], ep["port"]), file=stderr)
    if ep["domain"].startswith('[') and ep["domain"].endswith(']'):
        ep["domain"] = ep["domain"][1:-1]
    return ep, cli_args

def get_parameters(ep):
    head_block = get_current_block(ep)
    params = get_request(ep, "blockchain/parameters")
    return params, head_block

def manage_cmd(ep, cli_args):

    params, head_block = get_parameters(ep)
    if cli_args.subcmd == "about":
        about()
    elif cli_args.subcmd == "info":
        currency_info(ep)

    elif cli_args.subcmd == "diffi":
        difficulties(ep)

    elif cli_args.subcmd == "net" or cli_args.subcmd == "network":
        if cli_args.contains_switches("sort"):
            set_network_sort_keys(cli_args.get_definition("sort"))
        if cli_args.contains_switches("s"):
            set_network_sort_keys(cli_args.get_definition("s"))
        network_info(ep, cli_args.contains_switches("discover"))

    elif cli_args.subcmd == "issuers" and cli_args.subsubcmd and int(cli_args.subsubcmd) >= 0:
        list_issuers(ep, int(cli_args.subsubcmd), cli_args.contains_switches('last'))

    elif cli_args.subcmd == "argos":
        argos_info(ep)

    elif cli_args.subcmd == "amount" and cli_args.subsubcmd:
        cmd_amount(ep, cli_args)

    elif cli_args.subcmd == "tx" or cli_args.subcmd == "transaction":
        send_transaction(ep, cli_args)

    elif cli_args.subcmd == "cert":
        send_certification(ep, cli_args)

    elif cli_args.subcmd == "generate_auth_file":
        generate_auth_file(cli_args)

    elif cli_args.subcmd == "id" or cli_args.subcmd == "identities":
        id_pubkey_correspondence(ep, cli_args.subsubcmd)

    elif cli_args.subcmd == "wot":
        received_sent_certifications(ep, cli_args.subsubcmd)

    elif cli_args.subcmd == "license":
        display_license()


def about():
    print("\
\n             @@@@@@@@@@@@@\
\n         @@@     @         @@@\
\n      @@@   @@       @@@@@@   @@.           ", SILKAJ_VERSION, "\
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
\n            @@@@@@@@@@@@@@@\n")


