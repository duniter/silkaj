import datetime
import os
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

def difficulties(ep):
    current = get_current_block(ep)
    powmin, match = int(current["powMin"]), "`"
    while powmin > 0:
        if powmin >= 16: match += "0"; powmin -= 16
        else:
            end = "[0-" + hex(15 - powmin)[2:].upper() + "]"
            match += end; powmin = 0
    match += "*`"
    diffi = request(ep, "blockchain/difficulties")
    issuers, sorted_diffi = 0, sorted(diffi["levels"], key=itemgetter("level"))
    for d in diffi["levels"]:
        if d["level"] == current["powMin"]: issuers += 1
    os.system("clear")
    print("Minimal Proof-of-Work: {0} to match {1}\n### Difficulty to generate next block n°{2} for {3}/{4} nodes:\n{5}"
    .format(current["powMin"], match, diffi["block"], issuers, len(diffi["levels"]),
    tabulate(sorted_diffi, headers="keys", tablefmt="orgtbl")))

def network_info(ep):
    rows, columns = os.popen('stty size', 'r').read().split()
#    print(rows, columns) # debug
    wide = int(columns)
    if wide < 146:
        print("Wide screen need to be larger than 146. Current wide:", wide)
        exit()
    endpoints = discover_peers(ep)
    ### Todo : renommer endpoints en info ###
    diffi = request(ep, "blockchain/difficulties")
    i, members = 0, 0
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
    ### Todo: keep same columns order: issue on tabulate bitbucket ###
    print(tabulate(endpoints, headers="keys", tablefmt="orgtbl"))

def list_issuers(ep, nbr, last):
    current_nbr = get_current_block(ep)["number"]
    if nbr == 0: nbr = current_nbr
    blk_nbr, list_issuers = current_nbr, list()
    while (blk_nbr + nbr > current_nbr):
        print("{0:.0f}%: block n°{1}".format((current_nbr - blk_nbr) / nbr * 100, blk_nbr))
        issuer, issuer["block"] = dict(), blk_nbr
        issuer["pubkey"] = request(ep, "blockchain/block/" + str(blk_nbr))["issuer"]
        blk_nbr-=1
        list_issuers.append(issuer)
    for issuer in list_issuers:
        uid = get_uid_from_pubkey(ep, issuer["pubkey"])
        for issuer2 in list_issuers:
            if issuer2.get("pubkey") is not None and issuer.get("pubkey") is not None and \
                issuer2["pubkey"]  == issuer["pubkey"]:
                issuer2["uid"] = uid
                issuer2.pop("pubkey")
    os.system("clear")
    print("### Issuers for last", nbr, "blocks from block n°", current_nbr - nbr, "to block n°", current_nbr)
    if last or nbr <= 30:
        print(tabulate(list_issuers, headers="keys", tablefmt="orgtbl"))
    else:
    ## todo: requêttes possiblement bloquées par l’anti-spam DDOS des nœuds, faudrait passer en P2P: récupérer 200 blocs par nœuds.
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
        print(tabulate(sorted_list, headers="keys", tablefmt="orgtbl", floatfmt=".1f"))
