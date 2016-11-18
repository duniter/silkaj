import datetime
import os
from collections import OrderedDict
from tabulate import tabulate
from operator import itemgetter

from network_tools import *
from tools import *

def currency_info(ep):
    info_type = ["newcomers", "certs", "actives", "leavers", "excluded", "ud", "tx"]
    i, info_data = 0, dict()
    while (i < len(info_type)):
            info_data[info_type[i]] = request(ep, "blockchain/with/" + info_type[i])["result"]["blocks"]
            i +=1
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

def match_pattern(pow, match = '', π = 1):
    while pow > 0:
        if pow >= 16: match += "0"; pow -= 16; π *= 16
        else:
            match += "[0-" + hex(15 - pow)[2:].upper() + "]"
            π *= pow; pow = 0
    return (match + '*', π)

def power(nbr, pow = 0):
    while nbr >= 10: nbr /= 10; pow += 1
    return ("{0:.1f} × 10^{1}".format(nbr, pow))

def difficulties(ep):
    diffi = request(ep, "blockchain/difficulties")
    levels = [OrderedDict((i, d[i]) for i in ("uid", "level")) for d in diffi["levels"]]
    diffi["levels"] = levels
    current = get_current_block(ep)
    issuers, sorted_diffi = 0, sorted(diffi["levels"], key=itemgetter("level"))
    for d in diffi["levels"]:
        if d["level"] / 2 < current["powMin"]: issuers += 1
        d["match"] = match_pattern(d["level"])[0][:20]
        d["Π diffi"] = power(match_pattern(d["level"])[1])
        d["Σ diffi"] = d.pop("level")
    os.system("clear")
    print("Minimal Proof-of-Work: {0} to match `{1}`\n### Difficulty to generate next block n°{2} for {3}/{4} nodes:\n{5}"
    .format(current["powMin"], match_pattern(int(current["powMin"]))[0], diffi["block"], issuers, len(diffi["levels"]),
    tabulate(sorted_diffi, headers="keys", tablefmt="orgtbl", stralign="center")))

def network_info(ep, discover):
    rows, columns = os.popen('stty size', 'r').read().split()
#    print(rows, columns) # debug
    wide = int(columns)
    if wide < 146:
        print("Wide screen need to be larger than 146. Current wide:", wide)
        exit()
    # discover peers
    # and make sure fields are always ordered the same
    endpoints = [OrderedDict((i, p.get(i, None)) for i in ("domain", "port", "ip4", "ip6", "pubkey")) for p in discover_peers(ep, discover)]
    ### Todo : renommer endpoints en info ###
    diffi = request(ep, "blockchain/difficulties")
    i, members = 0, 0
    print("Getting informations about nodes:")
    while (i < len(endpoints)):
        print("{0:.0f}%".format(i/len(endpoints) * 100, 1), end = " ")
        best_ep = best_node(endpoints[i], 0)
        print(best_ep if best_ep is None else endpoints[i][best_ep], end = " ")
        print(endpoints[i]["port"])
        try:
            endpoints[i]["uid"] = get_uid_from_pubkey(ep, endpoints[i]["pubkey"])
            endpoints[i]["member"] = "yes"; members+=1
        except: pass
        if endpoints[i].get("member") is None: endpoints[i]["member"] = "no" 
        endpoints[i]["pubkey"] = endpoints[i]["pubkey"][:5] + "…"
### Todo: request difficulty from node point of view: two nodes with same pubkey id could be on diffrent branches and have different difficulties ###
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
            if wide > 171: endpoints[i]["mediantime"] = convert_time(current_blk["medianTime"], "hour")
            if wide > 185: endpoints[i]["difftime"] = convert_time(current_blk["time"] - current_blk["medianTime"], "hour")
            endpoints[i]["block"] = current_blk["number"]
            endpoints[i]["hash"] = current_blk["hash"][:10] + "…"
            endpoints[i]["version"] = request(endpoints[i], "node/summary")["duniter"]["version"]
        if endpoints[i].get("domain") is not None and len(endpoints[i]["domain"]) > 20:
            endpoints[i]["domain"] = "…" + endpoints[i]["domain"][-20:]
        if endpoints[i].get("ip6") is not None:
            if wide < 156: endpoints[i].pop("ip6")
            else: endpoints[i]["ip6"] = endpoints[i]["ip6"][:8] + "…"
        i+=1
    os.system("clear")
    print("###", len(endpoints), "peers ups, with", members, "members and", len(endpoints) - members,
    "non-members at", datetime.datetime.now().strftime("%H:%M:%S"))
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
        j+=1
    for pubkey in issuers_dict.keys():
        issuer = issuers_dict[pubkey]
        uid = get_uid_from_pubkey(ep, issuer["pubkey"])
        for issuer2 in list_issuers:
            if issuer2.get("pubkey") is not None and issuer.get("pubkey") is not None and \
                issuer2["pubkey"]  == issuer["pubkey"]:
                issuer2["uid"] = uid
                issuer2.pop("pubkey")
    os.system("clear")
    print("### Issuers for last {0} blocks from block n°{1} to block n°{2}".format(nbr, current_nbr - nbr + 1, current_nbr), end = " ")
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
                    found = 1; break
                j+=1
            if found == 0:
                issued = dict()
                issued["uid"] = list_issuers[i]["uid"]
                issued["blocks"] = 1
                list_issued.append(issued)
            i+=1
        i = 0
        while i < len(list_issued):
            list_issued[i]["percent"] = list_issued[i]["blocks"] / nbr * 100
            i+=1
        sorted_list = sorted(list_issued, key=itemgetter("blocks"), reverse=True)
        print("from {0} issuers\n{1}".format(len(list_issued),
        tabulate(sorted_list, headers="keys", tablefmt="orgtbl", floatfmt=".1f", stralign="center")))
