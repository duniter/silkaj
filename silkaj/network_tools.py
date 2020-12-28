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

from __future__ import unicode_literals
import re
import socket
import logging
from sys import exit, stderr
from asyncio import sleep
from duniterpy.api.client import Client
from duniterpy.api.bma import network
from duniterpy.constants import IPV4_REGEX, IPV6_REGEX

from silkaj.constants import (
    G1_DEFAULT_ENDPOINT,
    G1_TEST_DEFAULT_ENDPOINT,
    CONNECTION_TIMEOUT,
    ASYNC_SLEEP,
    FAILURE_EXIT_STATUS,
)


async def discover_peers(discover):
    """
    From first node, discover his known nodes.
    Remove from know nodes if nodes are down.
    If discover option: scan all network to know all nodes.
        display percentage discovering.
    """
    client = ClientInstance().client
    endpoints = await get_peers_among_leaves(client)
    if discover:
        print("Discovering network")
    for i, endpoint in enumerate(endpoints):
        if discover:
            print("{0:.0f}%".format(i / len(endpoints) * 100))
        if best_endpoint_address(endpoint, False) is None:
            endpoints.remove(endpoint)
        elif discover:
            endpoints = await recursive_discovering(endpoints, endpoint)
    return endpoints


async def recursive_discovering(endpoints, endpoint):
    """
    Discover recursively new nodes.
    If new node found add it and try to found new node from his known nodes.
    """
    api = generate_duniterpy_endpoint_format(endpoint)
    sub_client = Client(api)
    news = await get_peers_among_leaves(sub_client)
    await sub_client.close()
    for new in news:
        if best_endpoint_address(new, False) is not None and new not in endpoints:
            endpoints.append(new)
            await recursive_discovering(endpoints, new)
    return endpoints


async def get_peers_among_leaves(client):
    """
    Browse among leaves of peers to retrieve the other peers’ endpoints
    """
    leaves = await client(network.peers, leaves=True)
    peers = list()
    for leaf in leaves["leaves"]:
        await sleep(ASYNC_SLEEP + 0.05)
        leaf_response = await client(network.peers, leaf=leaf)
        peers.append(leaf_response["leaf"]["value"])
    return parse_endpoints(peers)


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


def generate_duniterpy_endpoint_format(ep):
    api = "BASIC_MERKLED_API " if ep["port"] != "443" else "BMAS "
    api += ep.get("domain") + " " if "domain" in ep else ""
    api += ep.get("ip4") + " " if "ip4" in ep else ""
    api += ep.get("ip6") + " " if "ip6" in ep else ""
    api += ep.get("port")
    return api


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class EndPoint(object):
    def __init__(self):
        ep = dict()
        try:
            from click.globals import get_current_context

            ctx = get_current_context()
            peer = ctx.obj["PEER"]
            gtest = ctx.obj["GTEST"]
        # To be activated when dropping Python 3.5
        # except (ModuleNotFoundError, RuntimeError):
        except:
            peer, gtest = None, None
        if peer:
            if ":" in peer:
                ep["domain"], ep["port"] = peer.rsplit(":", 1)
            else:
                ep["domain"], ep["port"] = peer, "443"
        else:
            ep["domain"], ep["port"] = (
                G1_TEST_DEFAULT_ENDPOINT if gtest else G1_DEFAULT_ENDPOINT
            )
        if ep["domain"].startswith("[") and ep["domain"].endswith("]"):
            ep["domain"] = ep["domain"][1:-1]
        self.ep = ep
        api = "BMAS" if ep["port"] == "443" else "BASIC_MERKLED_API"
        self.BMA_ENDPOINT = " ".join([api, ep["domain"], ep["port"]])


@singleton
class ClientInstance(object):
    def __init__(self):
        self.client = Client(EndPoint().BMA_ENDPOINT)


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
    if re.match(IPV4_REGEX, address) != None:
        return 4
    elif re.match(IPV6_REGEX, address) != None:
        return 6
    return 0


def best_endpoint_address(ep, main):
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
        exit(FAILURE_EXIT_STATUS)
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
