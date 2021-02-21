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

from click import command, option, argument, IntRange
from os import system
from collections import OrderedDict
from tabulate import tabulate
from operator import itemgetter
from asyncio import sleep
import aiohttp
from _socket import gaierror
import jsonschema

from duniterpy.api import bma

from silkaj.tools import coroutine
from silkaj.wot import identity_of
from silkaj.network_tools import (
    best_endpoint_address,
    EndPoint,
    ClientInstance,
)
from silkaj.blockchain_tools import HeadBlock
from silkaj.tools import CurrencySymbol
from silkaj.tui import convert_time
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
        ws = await client(bma.ws.block)
        while True:
            current = await ws.receive_json()
            jsonschema.validate(current, bma.ws.WS_BLOCK_SCHEMA)
            diffi = await client(bma.blockchain.difficulties)
            display_diffi(current, diffi)
        await client.close()

    except (aiohttp.WSServerHandshakeError, ValueError) as e:
        print("Websocket block {0} : {1}".format(type(e).__name__, str(e)))
    except (aiohttp.ClientError, gaierror, TimeoutError) as e:
        print("{0} : {1}".format(str(e), BMAS_ENDPOINT))
    except jsonschema.ValidationError as e:
        print("{:}:{:}".format(str(e.__class__.__name__), str(e)))


def display_diffi(current, diffi):
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
    blocks = await client(bma.blockchain.blocks, number, current_nbr - number + 1)
    issuers = list()
    issuers_dict = dict()
    for block in blocks:
        issuer = OrderedDict()
        issuer["pubkey"] = block["issuer"]
        if detailed or number <= 30:
            issuer["block"] = block["number"]
            issuer["gentime"] = convert_time(block["time"], "all")
            issuer["mediantime"] = convert_time(block["medianTime"], "all")
            issuer["hash"] = block["hash"][:10]
            issuer["powMin"] = block["powMin"]
        issuers_dict[issuer["pubkey"]] = issuer
        issuers.append(issuer)
    for pubkey in issuers_dict.keys():
        issuer = issuers_dict[pubkey]
        idty = await identity_of(issuer["pubkey"])
        for issuer2 in issuers:
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
        sorted_list = sorted(issuers, key=itemgetter("block"), reverse=True)
        print(
            "\n"
            + tabulate(
                sorted_list, headers="keys", tablefmt="orgtbl", stralign="center"
            )
        )
    else:
        list_issued = list()
        for issuer in issuers:
            found = False
            for issued in list_issued:
                if issued.get("uid") is not None and issued["uid"] == issuer["uid"]:
                    issued["blocks"] += 1
                    found = True
                    break
            if not found:
                issued = OrderedDict()
                issued["uid"] = issuer["uid"]
                issued["blocks"] = 1
                list_issued.append(issued)
        for issued in list_issued:
            issued["percent"] = issued["blocks"] / number * 100
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
    currency_symbol = await CurrencySymbol().symbol
    print(currency_symbol, "|")
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
        currency_symbol,
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
