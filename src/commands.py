import datetime
import time
import os
import sys
from collections import OrderedDict
from tabulate import tabulate
from operator import itemgetter

from network_tools import *
from tx import *
from auth import *
from tools import *
from constants import *


def currency_info(ep):
    info_type = ["newcomers", "certs", "actives", "leavers", "excluded", "ud", "tx"]
    i, info_data = 0, dict()
    while (i < len(info_type)):
            info_data[info_type[i]] = request(ep, "blockchain/with/" + info_type[i])["result"]["blocks"]
            i += 1
    current = get_current_block(ep)
    os.system("clear")
    print("Connected to node:", ep[best_node(ep, 1)], ep["port"],
    "\nCurrent block number:", current["number"],
    "\nCurrency name:", current["currency"],
    "\nNumber of members:", current["membersCount"],
    "\nMinimal Proof-of-Work:", current["powMin"],
    "\nCurrent time:", convert_time(current["time"], "all"),
    "\nMedian time:", convert_time(current["medianTime"], "all"),
    "\nDifference time:", convert_time(current["time"] - current["medianTime"], "hour"),
    "\nNumber of blocks containing: \
     \n- new comers:", len(info_data["newcomers"]),
    "\n- Certifications:", len(info_data["certs"]),
    "\n- Actives (members updating their membership):", len(info_data["actives"]),
    "\n- Leavers:", len(info_data["leavers"]),
    "\n- Excluded:", len(info_data["excluded"]),
    "\n- UD created:", len(info_data["ud"]),
    "\n- transactions:", len(info_data["tx"]))


def match_pattern(pow, match='', p=1):
    while pow > 0:
        if pow >= 16:
            match += "0"
            pow -= 16
            p *= 16
        else:
            match += "[0-" + hex(15 - pow)[2:].upper() + "]"
            p *= pow
            pow = 0
    return match + '*', p


def power(nbr, pow=0):
    while nbr >= 10:
        nbr /= 10
        pow += 1
    return "{0:.1f} × 10^{1}".format(nbr, pow)


def difficulties(ep):
    while True:
        diffi = request(ep, "blockchain/difficulties")
        levels = [OrderedDict((i, d[i]) for i in ("uid", "level")) for d in diffi["levels"]]
        diffi["levels"] = levels
        current = get_current_block(ep)
        issuers, sorted_diffi = 0, sorted(diffi["levels"], key=itemgetter("level"))
        for d in diffi["levels"]:
            if d["level"] / 2 < current["powMin"]:
                issuers += 1
            d["match"] = match_pattern(d["level"])[0][:20]
            d["Π diffi"] = power(match_pattern(d["level"])[1])
            d["Σ diffi"] = d.pop("level")
        os.system("clear")
        print("Minimal Proof-of-Work: {0} to match `{1}`\n### Difficulty to generate next block n°{2} for {3}/{4} nodes:\n{5}"
        .format(current["powMin"], match_pattern(int(current["powMin"]))[0], diffi["block"], issuers, len(diffi["levels"]),
        tabulate(sorted_diffi, headers="keys", tablefmt="orgtbl", stralign="center")))
        time.sleep(5)


network_sort_keys = ["block", "member", "diffi", "uid"]


def set_network_sort_keys(some_keys):
    global network_sort_keys
    if some_keys.endswith(","):
        print("Argument 'sort' ends with a comma, you have probably inserted a space after the comma, which is incorrect.")
        sys.exit(1)
    network_sort_keys = some_keys.split(",")


def get_network_sort_key(endpoint):
    t = list()
    for akey in network_sort_keys:
        if akey == 'diffi' or akey == 'block' or akey == 'port':
            t.append(int(endpoint[akey]) if akey in endpoint else 0)
        else:
            t.append(str(endpoint[akey]) if akey in endpoint else "")
    return tuple(t)


def network_info(ep, discover):
    rows, columns = os.popen('stty size', 'r').read().split()
#    print(rows, columns) # debug
    wide = int(columns)
    if wide < 146:
        print("Wide screen need to be larger than 146. Current wide:", wide)
        sys.exit(1)
    # discover peers
    # and make sure fields are always ordered the same
    endpoints = [OrderedDict((i, p.get(i, None)) for i in ("domain", "port", "ip4", "ip6", "pubkey")) for p in discover_peers(ep, discover)]
    # Todo : renommer endpoints en info
    diffi = request(ep, "blockchain/difficulties")
    i, members = 0, 0
    print("Getting informations about nodes:")
    while (i < len(endpoints)):
        print("{0:.0f}%".format(i/len(endpoints) * 100, 1), end=" ")
        best_ep = best_node(endpoints[i], 0)
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
#        diffi = request(endpoints[i], "blockchain/difficulties") # super long, doit être requetté uniquement pour les nœuds d’une autre branche
        for d in diffi["levels"]:
            if endpoints[i].get("uid") is not None:
                if endpoints[i]["uid"] == d["uid"]:
                    endpoints[i]["diffi"] = d["level"]
                if len(endpoints[i]["uid"]) > 10:
                    endpoints[i]["uid"] = endpoints[i]["uid"][:9] + "…"
        current_blk = get_current_block(endpoints[i])
        if current_blk is not None:
            endpoints[i]["gen_time"] = convert_time(current_blk["time"], "hour")
            if wide > 171:
                endpoints[i]["mediantime"] = convert_time(current_blk["medianTime"], "hour")
            if wide > 185:
                endpoints[i]["difftime"] = convert_time(current_blk["time"] - current_blk["medianTime"], "hour")
            endpoints[i]["block"] = current_blk["number"]
            endpoints[i]["hash"] = current_blk["hash"][:10] + "…"
            endpoints[i]["version"] = request(endpoints[i], "node/summary")["duniter"]["version"]
        if endpoints[i].get("domain") is not None and len(endpoints[i]["domain"]) > 20:
            endpoints[i]["domain"] = "…" + endpoints[i]["domain"][-20:]
        if endpoints[i].get("ip6") is not None:
            if wide < 156:
                endpoints[i].pop("ip6")
            else:
                endpoints[i]["ip6"] = endpoints[i]["ip6"][:8] + "…"
        i += 1
    os.system("clear")
    print("###", len(endpoints), "peers ups, with", members, "members and", len(endpoints) - members, "non-members at", datetime.datetime.now().strftime("%H:%M:%S"))
    endpoints = sorted(endpoints, key=get_network_sort_key)
    print(tabulate(endpoints, headers="keys", tablefmt="orgtbl", stralign="center"))


def list_issuers(ep, nbr, last):
    current_nbr = get_current_block(ep)["number"]
    url = "blockchain/blocks/" + str(nbr) + "/" + str(current_nbr - nbr + 1)
    blocks, list_issuers, j = request(ep, url), list(), 0
    issuers_dict = dict()
    while j < len(blocks):
        issuer = OrderedDict()
        issuer["pubkey"] = blocks[j]["issuer"]
        if last or nbr <= 30:
            issuer["block"] = blocks[j]["number"]
            issuer["gentime"] = convert_time(blocks[j]["time"], "hour")
            issuer["mediantime"] = convert_time(blocks[j]["medianTime"], "hour")
            issuer["hash"] = blocks[j]["hash"][:8]
        issuers_dict[issuer["pubkey"]] = issuer
        list_issuers.append(issuer)
        j += 1
    for pubkey in issuers_dict.keys():
        issuer = issuers_dict[pubkey]
        uid = get_uid_from_pubkey(ep, issuer["pubkey"])
        for issuer2 in list_issuers:
            if issuer2.get("pubkey") is not None and issuer.get("pubkey") is not None and \
                issuer2["pubkey"] == issuer["pubkey"]:
                issuer2["uid"] = uid
                issuer2.pop("pubkey")
    os.system("clear")
    print("### Issuers for last {0} blocks from block n°{1} to block n°{2}".format(nbr, current_nbr - nbr + 1, current_nbr), end=" ")
    if last or nbr <= 30:
        sorted_list = sorted(list_issuers, key=itemgetter("block"), reverse=True)
        print("\n{0}".format(tabulate(sorted_list, headers="keys", tablefmt="orgtbl", stralign="center")))
    else:
        i, list_issued = 0, list()
        while i < len(list_issuers):
            j, found = 0, 0
            while j < len(list_issued):
                if list_issued[j].get("uid") is not None and \
                    list_issued[j]["uid"] == list_issuers[i]["uid"]:
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
        print("from {0} issuers\n{1}".format(len(list_issued),
        tabulate(sorted_list, headers="keys", tablefmt="orgtbl", floatfmt=".1f", stralign="center")))


def cmd_amount(ep, c):
    if c.contains_definitions('pubkey'):
        pubkey = c.get_definition('pubkey')
        pubkey = check_public_key(pubkey)
        if not pubkey:
            return
    else:
        seed = auth_method(c)
        pubkey = get_publickey_from_seed(seed)

    show_amount_from_pubkey(ep, pubkey)


def cmd_transaction(ep, c):
    seed = auth_method(c)

    if not (c.contains_definitions('amount') or c.contains_definitions('amountDU')):
        print("--amount or --amountDU is not set")
        sys.exit(1)
    if not c.contains_definitions('output'):
        print("--output is not set")
        sys.exit(1)

    du = get_last_du_value(ep)
    if c.contains_definitions('amount'):
        amount = int(float(c.get_definition('amount')) * 100)
    if c.contains_definitions('amountDU'):
        amount = int(float(c.get_definition('amountDU')) * du)

    output = c.get_definition('output')

    if c.contains_definitions('comment'):
        comment = c.get_definition('comment')
    else:
        comment = ""

    if c.contains_switches('allSources'):
        allSources = True
    else:
        allSources = False

    if c.contains_definitions('outputBackChange'):
        outputBackChange = c.get_definition('outputBackChange')
    else:
        outputBackChange = None

    tx = list()
    currency_name = get_current_block(ep)["currency"]
    tx.append(["amount (" + currency_name + ")", amount / 100])
    tx.append(["amount (DU " + currency_name + ")", amount / du])
    pubkey = get_publickey_from_seed(seed)
    tx.append(["from", pubkey])
    id_from = get_uid_from_pubkey(ep, pubkey)
    if id_from is not NO_MATCHING_ID:
        tx.append(["from (id)", id_from])
    tx.append(["to", output])
    id_to = get_uid_from_pubkey(ep, output)
    if id_to is not NO_MATCHING_ID:
        tx.append(["to (id)", id_to])
    tx.append(["comment", comment])

    if c.contains_switches('yes') or c.contains_switches('y') or \
        input(tabulate(tx, tablefmt="fancy_grid") + \
        "\nDo you confirm sending this transaction? [yes/no]: ") == "yes":
        generate_and_send_transaction(ep, seed, amount, output, comment, allSources, outputBackChange)


def show_amount_from_pubkey(ep, pubkey):

    value = get_amount_from_pubkey(ep, pubkey)
    totalAmountInput = value[0]
    amount = value[1]
    # output
    DUvalue = get_last_du_value(ep)
    current_blk = get_current_block(ep)
    currency_name = str(current_blk["currency"])

    if totalAmountInput - amount != 0:
        print("Blockchain:")
        print("-----------")
        print("Relative     =", round(amount / DUvalue, 2), "DU", currency_name)
        print("Quantitative =",  round(amount / 100, 2), currency_name + "\n")

        print("Pending Transaction:")
        print("--------------------")
        print("Relative     =",  round((totalAmountInput - amount) / DUvalue, 2), "DU", currency_name)
        print("Quantitative =",  round((totalAmountInput - amount) / 100, 2), currency_name + "\n")

    print("Total amount of: " + pubkey)
    print("----------------------------------------------------------------")
    print("Total Relative     =",  round(totalAmountInput / DUvalue, 2), "DU", currency_name)
    print("Total Quantitative =",  round(totalAmountInput / 100, 2), currency_name + "\n")


def argos_info(ep):
    info_type = ["newcomers", "certs", "actives", "leavers", "excluded", "ud", "tx"]
    pretty_names = {'g1': 'Ğ1', 'gtest': 'Ğtest'}
    i, info_data = 0, dict()
    while (i < len(info_type)):
            info_data[info_type[i]] = request(ep, "blockchain/with/" + info_type[i])["result"]["blocks"]
            i += 1
    current = get_current_block(ep)
    pretty = current["currency"]
    if current["currency"] in pretty_names:
        pretty = pretty_names[current["currency"]]
    print(pretty, "|")
    print("---")
    href = 'href=http://%s:%s/' % (ep[best_node(ep, 1)], ep["port"])
    print("Connected to node:", ep[best_node(ep, 1)], ep["port"], "|", href,
    "\nCurrent block number:", current["number"],
    "\nCurrency name:", current["currency"],
    "\nNumber of members:", current["membersCount"],
    "\nMinimal Proof-of-Work:", current["powMin"],
    "\nCurrent time:", convert_time(current["time"], "all"),
    "\nMedian time:", convert_time(current["medianTime"], "all"),
    "\nDifference time:", convert_time(current["time"] - current["medianTime"], "hour"),
    "\nNumber of blocks containing… \
     \n-- new comers:", len(info_data["newcomers"]),
    "\n-- Certifications:", len(info_data["certs"]),
    "\n-- Actives (members updating their membership):", len(info_data["actives"]),
    "\n-- Leavers:", len(info_data["leavers"]),
    "\n-- Excluded:", len(info_data["excluded"]),
    "\n-- UD created:", len(info_data["ud"]),
    "\n-- transactions:", len(info_data["tx"]))


def id_pubkey_correspondence(ep, id_pubkey):
    if check_public_key(id_pubkey):
        print("{} public key corresponds to identity: {}".format(id_pubkey, get_uid_from_pubkey(ep, id_pubkey)))
    else:
        pubkeys = get_pubkeys_from_id(ep, id_pubkey)
        if pubkeys == NO_MATCHING_ID:
            print(NO_MATCHING_ID)
        else:
            print("Public keys found matching '{}':\n".format(id_pubkey))
            for pubkey in pubkeys:
                print("-", pubkey["pubkey"])
