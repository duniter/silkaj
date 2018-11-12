from datetime import datetime
from time import sleep
from os import system, popen
from collections import OrderedDict
from tabulate import tabulate
from operator import itemgetter

from silkaj.wot import get_uid_from_pubkey
from silkaj.network_tools import (
    discover_peers,
    get_request,
    best_node,
    EndPoint,
    HeadBlock,
)
from silkaj.tools import convert_time, message_exit, CurrencySymbol
from silkaj.constants import NO_MATCHING_ID


def currency_info():
    info_data = dict()
    for info_type in [
        "newcomers",
        "certs",
        "actives",
        "leavers",
        "excluded",
        "ud",
        "tx",
    ]:
        info_data[info_type] = get_request("blockchain/with/" + info_type)["result"][
            "blocks"
        ]
    head_block = HeadBlock().head_block
    ep = EndPoint().ep
    system("clear")
    print(
        "Connected to node:",
        ep[best_node(ep, False)],
        ep["port"],
        "\nCurrent block number:",
        head_block["number"],
        "\nCurrency name:",
        CurrencySymbol().symbol,
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
        "\nNumber of blocks containing: \
     \n- new comers:",
        len(info_data["newcomers"]),
        "\n- Certifications:",
        len(info_data["certs"]),
        "\n- Actives (members updating their membership):",
        len(info_data["actives"]),
        "\n- Leavers:",
        len(info_data["leavers"]),
        "\n- Excluded:",
        len(info_data["excluded"]),
        "\n- UD created:",
        len(info_data["ud"]),
        "\n- transactions:",
        len(info_data["tx"]),
    )


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


def difficulties():
    while True:
        diffi = get_request("blockchain/difficulties")
        levels = [
            OrderedDict((i, d[i]) for i in ("uid", "level")) for d in diffi["levels"]
        ]
        diffi["levels"] = levels
        current = get_request("blockchain/current")
        issuers = 0
        sorted_diffi = sorted(diffi["levels"], key=itemgetter("level"), reverse=True)
        for d in diffi["levels"]:
            if d["level"] / 2 < current["powMin"]:
                issuers += 1
            d["match"] = match_pattern(d["level"])[0][:20]
            d["Π diffi"] = power(match_pattern(d["level"])[1])
            d["Σ diffi"] = d.pop("level")
        system("clear")
        print(
            "Minimal Proof-of-Work: {0} to match `{1}`\nDifficulty to generate next block n°{2} for {3}/{4} nodes:\n{5}".format(
                current["powMin"],
                match_pattern(int(current["powMin"]))[0],
                diffi["block"],
                issuers,
                len(diffi["levels"]),
                tabulate(
                    sorted_diffi, headers="keys", tablefmt="orgtbl", stralign="center"
                ),
            )
        )
        sleep(5)


network_sort_keys = ["block", "member", "diffi", "uid"]


def set_network_sort_keys(some_keys):
    global network_sort_keys
    if some_keys.endswith(","):
        message_exit(
            "Argument 'sort' ends with a comma, you have probably inserted a space after the comma, which is incorrect."
        )
    network_sort_keys = some_keys.split(",")


def get_network_sort_key(endpoint):
    t = list()
    for akey in network_sort_keys:
        if akey == "diffi" or akey == "block" or akey == "port":
            t.append(int(endpoint[akey]) if akey in endpoint else 0)
        else:
            t.append(str(endpoint[akey]) if akey in endpoint else "")
    return tuple(t)


def network_info(discover):
    rows, columns = popen("stty size", "r").read().split()
    wide = int(columns)
    if wide < 146:
        message_exit("Wide screen need to be larger than 146. Current wide: " + wide)
    # discover peers
    # and make sure fields are always ordered the same
    endpoints = [
        OrderedDict(
            (i, p.get(i, None)) for i in ("domain", "port", "ip4", "ip6", "pubkey")
        )
        for p in discover_peers(discover)
    ]
    # Todo : renommer endpoints en info
    diffi = get_request("blockchain/difficulties")
    i, members = 0, 0
    print("Getting informations about nodes:")
    while i < len(endpoints):
        print("{0:.0f}%".format(i / len(endpoints) * 100, 1), end=" ")
        best_ep = best_node(endpoints[i], False)
        print(best_ep if best_ep is None else endpoints[i][best_ep], end=" ")
        print(endpoints[i]["port"])
        try:
            endpoints[i]["uid"] = get_uid_from_pubkey(ep, endpoints[i]["pubkey"])
            if endpoints[i]["uid"] is NO_MATCHING_ID:
                endpoints[i]["uid"] = None
            else:
                endpoints[i]["member"] = "yes"
                members += 1
        except:
            pass
        if endpoints[i].get("member") is None:
            endpoints[i]["member"] = "no"
        endpoints[i]["pubkey"] = endpoints[i]["pubkey"][:5] + "…"
        # Todo: request difficulty from node point of view: two nodes with same pubkey id could be on diffrent branches and have different difficulties
        #        diffi = get_request(endpoints[i], "blockchain/difficulties") # super long, doit être requetté uniquement pour les nœuds d’une autre branche
        for d in diffi["levels"]:
            if endpoints[i].get("uid") is not None:
                if endpoints[i]["uid"] == d["uid"]:
                    endpoints[i]["diffi"] = d["level"]
                if len(endpoints[i]["uid"]) > 10:
                    endpoints[i]["uid"] = endpoints[i]["uid"][:9] + "…"
        current_blk = get_request("blockchain/current", endpoints[i])
        if current_blk is not None:
            endpoints[i]["gen_time"] = convert_time(current_blk["time"], "hour")
            if wide > 171:
                endpoints[i]["mediantime"] = convert_time(
                    current_blk["medianTime"], "hour"
                )
            if wide > 185:
                endpoints[i]["difftime"] = convert_time(
                    current_blk["time"] - current_blk["medianTime"], "hour"
                )
            endpoints[i]["block"] = current_blk["number"]
            endpoints[i]["hash"] = current_blk["hash"][:10] + "…"
            endpoints[i]["version"] = get_request("node/summary", endpoints[i])[
                "duniter"
            ]["version"]
        if endpoints[i].get("domain") is not None and len(endpoints[i]["domain"]) > 20:
            endpoints[i]["domain"] = "…" + endpoints[i]["domain"][-20:]
        if endpoints[i].get("ip6") is not None:
            if wide < 156:
                endpoints[i].pop("ip6")
            else:
                endpoints[i]["ip6"] = endpoints[i]["ip6"][:8] + "…"
        i += 1
    system("clear")
    print(
        len(endpoints),
        "peers ups, with",
        members,
        "members and",
        len(endpoints) - members,
        "non-members at",
        datetime.now().strftime("%H:%M:%S"),
    )
    endpoints = sorted(endpoints, key=get_network_sort_key)
    print(tabulate(endpoints, headers="keys", tablefmt="orgtbl", stralign="center"))


def list_issuers(nbr, last):
    head_block = HeadBlock().head_block
    current_nbr = head_block["number"]
    if nbr == 0:
        nbr = head_block["issuersFrame"]
    url = "blockchain/blocks/" + str(nbr) + "/" + str(current_nbr - nbr + 1)
    blocks, list_issuers, j = get_request(url), list(), 0
    issuers_dict = dict()
    while j < len(blocks):
        issuer = OrderedDict()
        issuer["pubkey"] = blocks[j]["issuer"]
        if last or nbr <= 30:
            issuer["block"] = blocks[j]["number"]
            issuer["gentime"] = convert_time(blocks[j]["time"], "hour")
            issuer["mediantime"] = convert_time(blocks[j]["medianTime"], "hour")
            issuer["hash"] = blocks[j]["hash"][:10]
        issuers_dict[issuer["pubkey"]] = issuer
        list_issuers.append(issuer)
        j += 1
    for pubkey in issuers_dict.keys():
        issuer = issuers_dict[pubkey]
        uid = get_uid_from_pubkey(issuer["pubkey"])
        for issuer2 in list_issuers:
            if (
                issuer2.get("pubkey") is not None
                and issuer.get("pubkey") is not None
                and issuer2["pubkey"] == issuer["pubkey"]
            ):
                issuer2["uid"] = uid
                issuer2.pop("pubkey")
    system("clear")
    print(
        "Issuers for last {0} blocks from block n°{1} to block n°{2}".format(
            nbr, current_nbr - nbr + 1, current_nbr
        ),
        end=" ",
    )
    if last or nbr <= 30:
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
            list_issued[i]["percent"] = list_issued[i]["blocks"] / nbr * 100
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


def argos_info():
    info_type = ["newcomers", "certs", "actives", "leavers", "excluded", "ud", "tx"]
    pretty_names = {"g1": "Ğ1", "gtest": "Ğtest"}
    i, info_data = 0, dict()
    while i < len(info_type):
        info_data[info_type[i]] = get_request("blockchain/with/" + info_type[i])[
            "result"
        ]["blocks"]
        i += 1
    head_block = HeadBlock().head_block
    pretty = head_block["currency"]
    if head_block["currency"] in pretty_names:
        pretty = pretty_names[head_block["currency"]]
    print(pretty, "|")
    print("---")
    ep = EndPoint().ep
    href = "href=http://%s:%s/" % (ep[best_node(ep, False)], ep["port"])
    print(
        "Connected to node:",
        ep[best_node(ep, False)],
        ep["port"],
        "|",
        href,
        "\nCurrent block number:",
        head_block["number"],
        "\nCurrency name:",
        CurrencySymbol().symbol,
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
        "\nNumber of blocks containing… \
     \n-- new comers:",
        len(info_data["newcomers"]),
        "\n-- Certifications:",
        len(info_data["certs"]),
        "\n-- Actives (members updating their membership):",
        len(info_data["actives"]),
        "\n-- Leavers:",
        len(info_data["leavers"]),
        "\n-- Excluded:",
        len(info_data["excluded"]),
        "\n-- UD created:",
        len(info_data["ud"]),
        "\n-- transactions:",
        len(info_data["tx"]),
    )
