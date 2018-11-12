from __future__ import unicode_literals
from ipaddress import ip_address
from json import loads
import socket
import urllib.request
import logging
from sys import exit, stderr
from commandlines import Command

from silkaj.constants import (
    G1_DEFAULT_ENDPOINT,
    G1_TEST_DEFAULT_ENDPOINT,
    CONNECTION_TIMEOUT,
)


def discover_peers(discover):
    """
    From first node, discover his known nodes.
    Remove from know nodes if nodes are down.
    If discover option: scan all network to know all nodes.
        display percentage discovering.
    """
    endpoints = parse_endpoints(get_request("network/peers")["peers"])
    if discover:
        print("Discovering network")
    for i, endpoint in enumerate(endpoints):
        if discover:
            print("{0:.0f}%".format(i / len(endpoints) * 100))
        if best_node(endpoint, False) is None:
            endpoints.remove(endpoint)
        elif discover:
            endpoints = recursive_discovering(endpoints, endpoint)
    return endpoints


def recursive_discovering(endpoints):
    """
    Discover recursively new nodes.
    If new node found add it and try to found new node from his known nodes.
    """
    news = parse_endpoints(get_request("network/peers")["peers"])
    for new in news:
        if best_node(new, False) is not None and new not in endpoints:
            endpoints.append(new)
            recursive_discovering(endpoints, new)
    return endpoints


def parse_endpoints(rep):
    """
    endpoints[]{"domain", "ip4", "ip6", "pubkey"}
    list of dictionaries
    reps: raw endpoints
    """
    i, j, endpoints = 0, 0, []
    while i < len(rep):
        if rep[i]["status"] == "UP":
            while j < len(rep[i]["endpoints"]):
                ep = parse_endpoint(rep[i]["endpoints"][j])
                j += 1
                if ep is None:
                    break
                ep["pubkey"] = rep[i]["pubkey"]
                endpoints.append(ep)
        i += 1
        j = 0
    return endpoints


class EndPoint(object):
    __instance = None

    # Try to inheritate this part for all singleton classes
    def __new__(cls):
        if EndPoint.__instance is None:
            EndPoint.__instance = object.__new__(cls)
        return EndPoint.__instance

    def __init__(self):
        cli_args = Command()
        ep = dict()
        if cli_args.contains_switches("p"):
            ep["domain"], ep["port"] = cli_args.get_definition("p").rsplit(":", 1)
        else:
            ep["domain"], ep["port"] = (
                G1_TEST_DEFAULT_ENDPOINT
                if cli_args.contains_switches("gtest")
                else G1_DEFAULT_ENDPOINT
            )
        if ep["domain"].startswith("[") and ep["domain"].endswith("]"):
            ep["domain"] = ep["domain"][1:-1]
        self.ep = ep


def parse_endpoint(rep):
    """
    rep: raw endpoint, sep: split endpoint
    domain, ip4 or ip6 could miss on raw endpoint
    """
    ep, sep = {}, rep.split(" ")
    if sep[0] == "BASIC_MERKLED_API":
        if check_port(sep[-1]):
            ep["port"] = sep[-1]
        if (
            len(sep) == 5
            and check_ip(sep[1]) == 0
            and check_ip(sep[2]) == 4
            and check_ip(sep[3]) == 6
        ):
            ep["domain"], ep["ip4"], ep["ip6"] = sep[1], sep[2], sep[3]
        if len(sep) == 4:
            ep = endpoint_type(sep[1], ep)
            ep = endpoint_type(sep[2], ep)
        if len(sep) == 3:
            ep = endpoint_type(sep[1], ep)
        return ep
    else:
        return None


def endpoint_type(sep, ep):
    typ = check_ip(sep)
    if typ == 0:
        ep["domain"] = sep
    elif typ == 4:
        ep["ip4"] = sep
    elif typ == 6:
        ep["ip6"] = sep
    return ep


def check_ip(address):
    try:
        return ip_address(address).version
    except:
        return 0


def get_request(path, ep=EndPoint().ep):
    address = best_node(ep, False)
    if address is None:
        return address
    url = "http://" + ep[address] + ":" + ep["port"] + "/" + path
    if ep["port"] == "443":
        url = "https://" + ep[address] + "/" + path
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request, timeout=CONNECTION_TIMEOUT)
    encoding = response.info().get_content_charset("utf8")
    return loads(response.read().decode(encoding))


def post_request(path, postdata, ep=EndPoint().ep):
    address = best_node(ep, False)
    if address is None:
        return address
    url = "http://" + ep[address] + ":" + ep["port"] + "/" + path
    if ep["port"] == "443":
        url = "https://" + ep[address] + "/" + path
    request = urllib.request.Request(url, bytes(postdata, "utf-8"))
    try:
        response = urllib.request.urlopen(request, timeout=CONNECTION_TIMEOUT)
    except urllib.error.URLError as e:
        print(e, file=stderr)
        exit(1)
    encoding = response.info().get_content_charset("utf8")
    return loads(response.read().decode(encoding))


def best_node(ep, main):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(CONNECTION_TIMEOUT)
    addresses, port = ("domain", "ip6", "ip4"), int(ep["port"])
    for address in addresses:
        if address in ep:
            try:
                s.connect((ep[address], port))
                s.close()
                return address
            except Exception as e:
                logging.debug(
                    "Connection to endpoint %s (%s) failled (%s)" % (ep, address, e)
                )
    if main:
        print("Wrong node given as argument", file=stderr)
        exit(1)
    return None


def check_port(port):
    try:
        port = int(port)
    except:
        print("Port must be an integer", file=stderr)
        return False
    if port < 0 or port > 65536:
        print("Wrong port number", file=stderr)
        return False
    return True


class HeadBlock(object):
    __instance = None

    def __new__(cls):
        if HeadBlock.__instance is None:
            HeadBlock.__instance = object.__new__(cls)
        return HeadBlock.__instance

    def __init__(self):
        self.head_block = get_request("blockchain/current")
