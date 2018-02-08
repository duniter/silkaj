#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from commandlines import Command
from tx import send_transaction
from commands import *
from wot import *
from constants import SILKAJ_VERSION


def usage():
    print("Silkaj: command line Duniter client \
    \n\nhelp: -h, --help, --usage \
    \nversion: -v, --version \
    \n \
    \nCustom endpoint with option `-p` and <domain>:<port>\
    \n \
    \nCommands: \
    \n - info: Display information about currency \
    \n \
    \n - amount: Get amount of accounts \
    \n      --pubkeys=<pubkey:pubkey:pubkey>\
    \n      --auth-scrypt [script parameters -n <N> -r <r> -p <p>] (default: 4096,16,1)\
    \n      --auth-seed | --auth-file [--file=<path file>] | --auth-wif\
    \n \
    \n - tx/transaction: Send transaction\
    \n     - authentication:\
    \n         --auth-scrypt [script parameters -n <N> -r <r> -p <p>] (default: 4096,16,1)\
    \n         --auth-seed | --auth-file [--file=<path file>] | --auth-wif\
    \n     - amount:\
    \n         --amountUD=<relative value> | --amount=<quantitative value>\
    \n         [--allSources] \
    \n     --output=<public key>[:checksum] \
    \n     [--comment=<comment>] \
    \n     [--outputBackChange=<public key[:checksum]>] \
    \n     [-y | --yes], don't ask for prompt confirmation \
    \n \
    \n - net/network: Display current network with many information \
    \n      [--discover]     Discover all network (could take a while), optional \
    \n      [-s | --sort]     Sort column names comma-separated (for example \"-s block,diffi\"), optional \
    \n                       Default sort is block,member,diffi,uid \
    \n \
    \n - diffi: list proof-of-work difficulty to generate next block \
    \n \
    \n - issuers n: display last n issuers (`0` for all blockchain) \
    \n      last issuers are displayed under n <= 30.\
    \n      To force display last ones, use `--last` option\
    \n \
    \n - argos: display currency information formated for Argos or BitBar\
    \n \
    \n - generate_auth_file: Generate file to store the seed of the account\
    \n      --auth-scrypt [script parameters -n <N> -r <r> -p <p>] (default: 4096,16,1)\
    \n      --auth-seed | --auth-file [--file=<path file>] | --auth-wif\
    \n \
    \n - id/identities <pubkey> or <identity>: get corresponding identity or pubkey from pubkey or identity.\
    \n      it could autocomplete the pubkey corresponding to an identity with three or four following characters.\
    \n \
    \n - wot <pubkey> or <identity>: display received and sent certifications for an account.")
    sys.exit()


def cli():
    # ep: endpoint, node's network interface
    ep, cli_args = dict(), Command()
    subcmd = ["info", "diffi", "net", "network", "issuers", "argos", "amount", "tx", "transaction", "generate_auth_file", "id", "identities", "wot"]
    if cli_args.is_version_request():
        print(SILKAJ_VERSION)
        sys.exit()
    if cli_args.is_help_request() or cli_args.is_usage_request() or cli_args.subcmd not in subcmd:
        usage()
    ep["domain"], ep["port"] = "g1.duniter.org", "443"
    try:
        ep["domain"], ep["port"] = cli_args.get_definition('p').rsplit(':', 1)
    except:
        print("Requested default node: <{}:{}>".format(ep["domain"], ep["port"]), file=sys.stderr)
    if ep["domain"].startswith('[') and ep["domain"].endswith(']'):
        ep["domain"] = ep["domain"][1:-1]
    return ep, cli_args


def manage_cmd(ep, c):
    if cli_args.subcmd == "info":
        currency_info(ep)

    elif cli_args.subcmd == "diffi":
        difficulties(ep)

    elif cli_args.subcmd == "net" or cli_args.subcmd == "network":
        from commands import set_network_sort_keys
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

    elif cli_args.subcmd == "generate_auth_file":
        generate_auth_file(cli_args)

    elif cli_args.subcmd == "id" or cli_args.subcmd == "identities":
        id_pubkey_correspondence(ep, cli_args.subsubcmd)

    elif cli_args.subcmd == "wot":
        received_sent_certifications(ep, cli_args.subsubcmd)


if __name__ == '__main__':
    ep, cli_args = cli()
    check_port(ep["port"])
    best_node(ep, 1)
    manage_cmd(ep, cli_args)
