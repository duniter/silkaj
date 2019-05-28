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

from click import command, option, argument, IntRange, get_terminal_size
from datetime import datetime
from os import system, popen
from collections import OrderedDict
from tabulate import tabulate
from operator import itemgetter
from asyncio import sleep
import aiohttp
from _socket import gaierror
import jsonschema

from duniterpy.api.client import Client, parse_text
from duniterpy.api.bma import blockchain, node, ws

from silkaj.tools import coroutine
from silkaj.wot import identity_of
from silkaj.network_tools import (
    discover_peers,
    best_endpoint_address,
    EndPoint,
    ClientInstance,
    HeadBlock,
)
from silkaj.tools import convert_time, message_exit, CurrencySymbol
from silkaj.constants import ASYNC_SLEEP


@command("info", help="Display information about currency")
@coroutine
async def currency_info():
    head_block = await HeadBlock().head_block
    ep = EndPoint().ep
    print(
        "Connected to node:",
        ep[best_endpoint_address(ep, False)],
        ep["port"],
        "\nCurrent block number:",
        head_block["number"],
        "\nCurrency name:",
        await CurrencySymbol().symbol,
        "\nNumber of members:",
        head_block["membersCount"],
        "\nMinimal Proof-of-Work:",
        head_block["powMin"],
        "\nCurrent time:",
        convert_time(head_block["time"], "all"),
        "\nMedian time:",
        convert_time(head_block["medianTime"], "all"),
        "\nDifference time:",
        convert_time(head_block["time"] - head_block["medianTime"], "hour"),
    )
    client = ClientInstance().client
    await client.close()


def match_pattern(pow, match="", p=1):
    while pow > 0:
        if pow >= 16:
            match += "0"
            pow -= 16
            p *= 16
        else:
            match += "[0-" + hex(15 - pow)[2:].upper() + "]"
            p *= pow
            pow = 0
    return match + "*", p


def power(nbr, pow=0):
    while nbr >= 10:
        nbr /= 10
        pow += 1
    return "{0:.1f} × 10^{1}".format(nbr, pow)


@command(
    "diffi",
    help="Display the current Proof of Work difficulty level to generate the next block",
)
@coroutine
async def difficulties():
    client = ClientInstance().client
    try:
        ws_connection = client(ws.block)
        async with ws_connection as ws_c:
            async for msg in ws_c:
                if msg.type == aiohttp.WSMsgType.CLOSED:
                    message_exit("Web socket connection closed!")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    message_exit("Web socket connection error!")
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    current = parse_text(msg.data, ws.WS_BLOCK_SCHEMA)
                    diffi = await client(blockchain.difficulties)
                    await display_diffi(current, diffi)

    except (aiohttp.WSServerHandshakeError, ValueError) as e:
        print("Websocket block {0} : {1}".format(type(e).__name__, str(e)))
    except (aiohttp.ClientError, gaierror, TimeoutError) as e:
        print("{0} : {1}".format(str(e), BMAS_ENDPOINT))
    except jsonschema.ValidationError as e:
        print("{:}:{:}".format(str(e.__class__.__name__), str(e)))


async def display_diffi(current, diffi):
    levels = [OrderedDict((i, d[i]) for i in ("uid", "level")) for d in diffi["levels"]]
    diffi["levels"] = levels
    issuers = 0
    sorted_diffi = sorted(diffi["levels"], key=itemgetter("level"), reverse=True)
    for d in diffi["levels"]:
        if d["level"] / 2 < current["powMin"]:
            issuers += 1
        d["match"] = match_pattern(d["level"])[0][:20]
        d["Π diffi"] = power(match_pattern(d["level"])[1])
        d["Σ diffi"] = d.pop("level")
    system("cls||clear")
    print(
        "Current block: n°{0}, generated on the {1}\n\
Generation of next block n°{2} possible by at least {3}/{4} members\n\
Common Proof-of-Work difficulty level: {5}, hash starting with `{6}`\n{7}".format(
            current["number"],
            convert_time(current["time"], "all"),
            diffi["block"],
            issuers,
            len(diffi["levels"]),
            current["powMin"],
            match_pattern(int(current["powMin"]))[0],
            tabulate(
                sorted_diffi, headers="keys", tablefmt="orgtbl", stralign="center"
            ),
        )
    )


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
    diffi = await client(blockchain.difficulties)
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
        current_blk = await sub_client(blockchain.current)
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
            summary = await sub_client(node.summary)
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


@command("blocks", help="Display blocks: default: 0 for current window size")
@argument("number", default=0, type=IntRange(0, 5000))
@option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Force detailed view. Compact view happen over 30 blocks",
)
@coroutine
async def list_blocks(number, detailed):
    head_block = await HeadBlock().head_block
    current_nbr = head_block["number"]
    if number == 0:
        number = head_block["issuersFrame"]
    client = ClientInstance().client
    blocks = await client(blockchain.blocks, number, current_nbr - number + 1)
    list_issuers, j = list(), 0
    issuers_dict = dict()
    while j < len(blocks):
        issuer = OrderedDict()
        issuer["pubkey"] = blocks[j]["issuer"]
        if detailed or number <= 30:
            issuer["block"] = blocks[j]["number"]
            issuer["gentime"] = convert_time(blocks[j]["time"], "all")
            issuer["mediantime"] = convert_time(blocks[j]["medianTime"], "all")
            issuer["hash"] = blocks[j]["hash"][:10]
        issuers_dict[issuer["pubkey"]] = issuer
        list_issuers.append(issuer)
        j += 1
    for pubkey in issuers_dict.keys():
        issuer = issuers_dict[pubkey]
        idty = await identity_of(issuer["pubkey"])
        for issuer2 in list_issuers:
            if (
                issuer2.get("pubkey") is not None
                and issuer.get("pubkey") is not None
                and issuer2["pubkey"] == issuer["pubkey"]
            ):
                issuer2["uid"] = idty["uid"]
                issuer2.pop("pubkey")
        await sleep(ASYNC_SLEEP)
    await client.close()
    print(
        "Last {0} blocks from n°{1} to n°{2}".format(
            number, current_nbr - number + 1, current_nbr
        ),
        end=" ",
    )
    if detailed or number <= 30:
        sorted_list = sorted(list_issuers, key=itemgetter("block"), reverse=True)
        print(
            "\n"
            + tabulate(
                sorted_list, headers="keys", tablefmt="orgtbl", stralign="center"
            )
        )
    else:
        i, list_issued = 0, list()
        while i < len(list_issuers):
            j, found = 0, 0
            while j < len(list_issued):
                if (
                    list_issued[j].get("uid") is not None
                    and list_issued[j]["uid"] == list_issuers[i]["uid"]
                ):
                    list_issued[j]["blocks"] += 1
                    found = 1
                    break
                j += 1
            if found == 0:
                issued = OrderedDict()
                issued["uid"] = list_issuers[i]["uid"]
                issued["blocks"] = 1
                list_issued.append(issued)
            i += 1
        i = 0
        while i < len(list_issued):
            list_issued[i]["percent"] = list_issued[i]["blocks"] / number * 100
            i += 1
        sorted_list = sorted(list_issued, key=itemgetter("blocks"), reverse=True)
        print(
            "from {0} issuers\n{1}".format(
                len(list_issued),
                tabulate(
                    sorted_list,
                    headers="keys",
                    tablefmt="orgtbl",
                    floatfmt=".1f",
                    stralign="center",
                ),
            )
        )


@command("argos", help="Display currency information formatted for Argos or BitBar")
@coroutine
async def argos_info():
    head_block = await HeadBlock().head_block
    print(await CurrencySymbol().symbol, "|")
    print("---")
    ep = EndPoint().ep
    endpoint_address = ep[best_endpoint_address(ep, False)]
    if ep["port"] == "443":
        href = "href=https://%s/" % (endpoint_address)
    else:
        href = "href=http://%s:%s/" % (endpoint_address, ep["port"])
    print(
        "Connected to node:",
        ep[best_endpoint_address(ep, False)],
        ep["port"],
        "|",
        href,
        "\nCurrent block number:",
        head_block["number"],
        "\nCurrency name:",
        await CurrencySymbol().symbol,
        "\nNumber of members:",
        head_block["membersCount"],
        "\nMinimal Proof-of-Work:",
        head_block["powMin"],
        "\nCurrent time:",
        convert_time(head_block["time"], "all"),
        "\nMedian time:",
        convert_time(head_block["medianTime"], "all"),
        "\nDifference time:",
        convert_time(head_block["time"] - head_block["medianTime"], "hour"),
    )
    client = ClientInstance().client
    await client.close()
