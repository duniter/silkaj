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

"""
from click import command, option, get_terminal_size
from datetime import datetime
from os import system
from collections import OrderedDict
from tabulate import tabulate
from asyncio import sleep

from duniterpy.api.client import Client
from duniterpy.api import bma

from silkaj.tools import coroutine
from silkaj.wot import identity_of
from silkaj.network_tools import (
    discover_peers,
    best_endpoint_address,
    ClientInstance,
)
from silkaj.tools import message_exit
from silkaj.tui import convert_time
from silkaj.constants import ASYNC_SLEEP


def get_network_sort_key(endpoint):
    t = list()
    for akey in network_sort_keys:
        if akey == "diffi" or akey == "block" or akey == "port":
            t.append(int(endpoint[akey]) if akey in endpoint else 0)
        else:
            t.append(str(endpoint[akey]) if akey in endpoint else "")
    return tuple(t)


@command("net", help="Display network view")
@option(
    "--discover", "-d", is_flag=True, help="Discover the network (could take a while)"
)
@option(
    "--sort",
    "-s",
    default="block,member,diffi,uid",
    show_default=True,
    help="Sort column names comma-separated",
)
@coroutine
async def network_info(discover, sort):
    global network_sort_keys
    network_sort_keys = sort.split(",")
    width = get_terminal_size()[0]
    if width < 146:
        message_exit(
            "Wide screen need to be larger than 146. Current width: " + str(width)
        )
    # discover peers
    # and make sure fields are always ordered the same
    infos = [
        OrderedDict(
            (i, p.get(i, None)) for i in ("domain", "port", "ip4", "ip6", "pubkey")
        )
        for p in await discover_peers(discover)
    ]
    client = ClientInstance().client
    diffi = await client(bma.blockchain.difficulties)
    members = 0
    print("Getting informations about nodes:")
    for i, info in enumerate(infos):
        ep = info
        api = "BASIC_MERKLED_API " if ep["port"] != "443" else "BMAS "
        api += ep.get("domain") + " " if ep["domain"] else ""
        api += ep.get("ip4") + " " if ep["ip4"] else ""
        api += ep.get("ip6") + " " if ep["ip6"] else ""
        api += ep.get("port")
        print("{0:.0f}%".format(i / len(infos) * 100, 1), end=" ")
        best_ep = best_endpoint_address(info, False)
        print(best_ep if best_ep is None else info[best_ep], end=" ")
        print(info["port"])
        await sleep(ASYNC_SLEEP)
        try:
            info["uid"] = await identity_of(info["pubkey"])
            info["uid"] = info["uid"]["uid"]
            info["member"] = "yes"
            members += 1
        except:
            info["uid"] = None
            info["member"] = "no"
        info["pubkey"] = info["pubkey"][:5] + "…"
        for d in diffi["levels"]:
            if info.get("uid") is not None:
                if info["uid"] == d["uid"]:
                    info["diffi"] = d["level"]
                if len(info["uid"]) > 10:
                    info["uid"] = info["uid"][:9] + "…"
        sub_client = Client(api)
        current_blk = await sub_client(bma.blockchain.current)
        if current_blk is not None:
            info["gen_time"] = convert_time(current_blk["time"], "hour")
            if width > 171:
                info["mediantime"] = convert_time(current_blk["medianTime"], "hour")
            if width > 185:
                info["difftime"] = convert_time(
                    current_blk["time"] - current_blk["medianTime"], "hour"
                )
            info["block"] = current_blk["number"]
            info["hash"] = current_blk["hash"][:10] + "…"
            summary = await sub_client(bma.node.summary)
            info["version"] = summary["duniter"]["version"]
        await sub_client.close()
        if info.get("domain") is not None and len(info["domain"]) > 20:
            info["domain"] = "…" + info["domain"][-20:]
        if info.get("ip6") is not None:
            if width < 156:
                info.pop("ip6")
            else:
                info["ip6"] = info["ip6"][:8] + "…"
    await client.close()
    print(
        len(infos),
        "peers ups, with",
        members,
        "members and",
        len(infos) - members,
        "non-members at",
        datetime.now().strftime("%H:%M:%S"),
    )
    infos = sorted(infos, key=get_network_sort_key)
    print(tabulate(infos, headers="keys", tablefmt="orgtbl", stralign="center"))

"""
