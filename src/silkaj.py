#!/usr/bin/env python3

import os

from commandlines import Command

from commands import *

def cli():
    # ep: endpoint, node's network interface
    ep, c = dict(), Command()
    ep["domain"], ep["port"] = "duniter.org", "8999"
    try: ep["domain"], ep["port"] = c.get_definition('p').split(':')
    except: pass
    try: ep["domain"], ep["port"] = c.get_definition('peer').split(':')
    except: pass
    if c.is_help_request() or c.is_usage_request(): usage()
    if c.is_version_request(): print("silkaj 0.1.0")
    return (ep, c)

def manage_cmd(ep, c):
    if c.subcmd == "info":
       currency_info(ep)
    elif c.subcmd == "diffi":
        difficulties(ep)
    elif c.subcmd == "network":
        rows, columns = os.popen('stty size', 'r').read().split()
#        print(rows, columns) # debug
        if int(columns) >= 146: network_info(ep, int(columns))
        else: print("Current wide screen need to be larger than 146. Current wide:", columns)
    elif c.subcmd == "issuers" and c.subsubcmd and int(c.subsubcmd) >= 0:
        list_issuers(ep, int(c.subsubcmd), c.contains_switches('last'))
    else: usage()

def usage():
    print("Silkaj: command line Duniter client \
    \n\nhelp: -h, --help, --usage \
    \nversion: -v, --version \
    \ncommands: \
    \n - info: display information about currency \
    \n - diffi: list proof-of-work difficulty to generate next block \
    \n - network: display current network with many information \
    \n - issuers n: display last n issuers (`0` for all blockchain) \
    \n  - last issuers are displayed under n <= 30. To force display last ones, use `--last` option \
    \ncustom endpoint with options `-p` or `--peer` and <domain>:<port>")
    exit()

if __name__ == '__main__':
    os.system("clear")
    ep, c = cli()
    check_port(ep["port"])
    best_node(ep, 1)
    manage_cmd(ep, c)
