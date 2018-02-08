import os
import sys
from tabulate import tabulate
from collections import OrderedDict

from network_tools import get_request
from tools import get_pubkeys_from_id
from constants import *


def get_sent_certifications(certs):
    sent = list()
    if certs["signed"]:
        for cert in certs["signed"]:
            sent.append(cert["uid"])
    return sent


def received_sent_certifications(ep, id):
    """
    check id exist
    many identities could exist
    retrieve the one searched
    get id of received and sent certifications
    display on a chart the result with the numbers
    """
    if get_pubkeys_from_id(ep, id) == NO_MATCHING_ID:
        print(NO_MATCHING_ID)
        sys.exit(1)
    certs_req = get_request(ep, "wot/lookup/" + id)["results"][0]
    certifications = OrderedDict()
    os.system("clear")
    for certs in certs_req["uids"]:
        if certs["uid"].lower() == id.lower():
            certifications["received"] = list()
            for cert in certs["others"]:
                certifications["received"].append(cert["uids"][0])
            certifications["sent"] = get_sent_certifications(certs_req)
            print("{0} ({1}) from block #{2}\nreceived {3} and sent {4} certifications:\n{5}\n"
                    .format(id, certs_req["pubkey"][:5] + "…", certs["meta"]["timestamp"][:15] + "…",
                        len(certifications["received"]), len(certifications["sent"]),
                        tabulate(certifications, headers="keys", tablefmt="orgtbl", stralign="center")))
