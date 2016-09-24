import datetime

from network_tools import *

def convert_time(timestamp, kind):
    ts = int(timestamp)
    if kind == "all": pattern = "%Y-%m-%d %H:%M:%S"
    elif kind == "hour":
        if ts >= 3600: pattern = "%H:%M:%S"
        else: pattern = "%M:%S"
    return (datetime.datetime.fromtimestamp(ts).strftime(pattern))

def get_uid_from_pubkey(ep, pubkey):
    i, results = 0, request(ep, "wot/lookup/" + pubkey)["results"]
    if results == None: return(None)
    while (i < len(results)):
        if results[i]["uids"][0]["uid"] != pubkey:
            return (results[i]["uids"][0]["uid"])
        i+=1

def get_current_block(ep):
    current_blk = request(ep, "blockchain/current")
    if current_blk is None: return (None)
    else: return (current_blk)
