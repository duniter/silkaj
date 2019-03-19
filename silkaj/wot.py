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

from click import command, argument
from time import time
from tabulate import tabulate
from collections import OrderedDict
from duniterpy.api.bma import wot, blockchain

from silkaj.network_tools import ClientInstance
from silkaj.crypto_tools import check_public_key
from silkaj.tools import message_exit, convert_time, coroutine
from silkaj.blockchain_tools import BlockchainParams
from silkaj.constants import NO_MATCHING_ID


def get_sent_certifications(certs, time_first_block, params):
    sent = list()
    expire = list()
    if certs["signed"]:
        for cert in certs["signed"]:
            sent.append(cert["uid"])
            expire.append(
                expiration_date_from_block_id(
                    cert["cert_time"]["block"], time_first_block, params
                )
            )
    return sent, expire


@command(
    "wot",
    help="Check received and sent certifications and consult the membership status of any given identity",
)
@argument("id")
@coroutine
async def received_sent_certifications(id):
    """
    get searched id
    get id of received and sent certifications
    display on a chart the result with the numbers
    """
    client = ClientInstance().client
    first_block = await client(blockchain.block, 1)
    time_first_block = first_block["time"]
    id_certs = await get_informations_for_identity(id)
    certifications = OrderedDict()
    params = await BlockchainParams().params
    for certs in id_certs["uids"]:
        if certs["uid"].lower() == id.lower():
            pubkey = id_certs["pubkey"]
            req = await client(wot.requirements, pubkey)
            req = req["identities"][0]
            certifications["received_expire"] = list()
            certifications["received"] = list()
            for cert in certs["others"]:
                certifications["received_expire"].append(
                    expiration_date_from_block_id(
                        cert["meta"]["block_number"], time_first_block, params
                    )
                )
                certifications["received"].append(
                    cert_written_in_the_blockchain(req["certifications"], cert)
                )
                certifications["sent"], certifications[
                    "sent_expire"
                ] = get_sent_certifications(id_certs, time_first_block, params)
            nbr_sent_certs = (
                len(certifications["sent"]) if "sent" in certifications else 0
            )
            print(
                "{0} ({1}) from block #{2}\nreceived {3} and sent {4}/{5} certifications:\n{6}\n{7}\n".format(
                    id,
                    pubkey[:5] + "…",
                    certs["meta"]["timestamp"][:15] + "…",
                    len(certifications["received"]),
                    nbr_sent_certs,
                    params["sigStock"],
                    tabulate(
                        certifications,
                        headers="keys",
                        tablefmt="orgtbl",
                        stralign="center",
                    ),
                    "✔: Certifications written into the blockchain",
                )
            )
            await membership_status(certifications, certs, pubkey, req)
    await client.close()


def cert_written_in_the_blockchain(written_certs, certifieur):
    for cert in written_certs:
        if cert["from"] == certifieur["pubkey"]:
            return certifieur["uids"][0] + " ✔"
    return certifieur["uids"][0]


async def membership_status(certifications, certs, pubkey, req):
    params = await BlockchainParams().params
    if len(certifications["received"]) >= params["sigQty"]:
        print(
            "Membership expiration due to certification expirations: "
            + certifications["received_expire"][
                len(certifications["received"]) - params["sigQty"]
            ]
        )
    member = await is_member(pubkey, certs["uid"])
    print("member:", member)
    if req["revoked"]:
        print(
            "revoked:",
            req["revoked"],
            "\nrevoked on:",
            convert_time(req["revoked_on"], "date") + "\n",
        )
    if not member and req["wasMember"]:
        print("expired:", req["expired"], "\nwasMember:", req["wasMember"])
    elif member:
        print(
            "Membership document expiration: "
            + convert_time(time() + req["membershipExpiresIn"], "date")
        )
        print("Sentry:", req["isSentry"])
    print("outdistanced:", req["outdistanced"])


def expiration_date_from_block_id(block_id, time_first_block, params):
    return convert_time(
        date_approximation(block_id, time_first_block, params["avgGenTime"])
        + params["sigValidity"],
        "date",
    )


def date_approximation(block_id, time_first_block, avgentime):
    return time_first_block + block_id * avgentime


@command("id", help="Find corresponding identity or pubkey from pubkey or identity")
@argument("id_pubkey")
@coroutine
async def id_pubkey_correspondence(id_pubkey):
    client = ClientInstance().client
    if check_public_key(id_pubkey, False):
        print(
            "{} public key corresponds to identity: {}".format(
                id_pubkey, await get_uid_from_pubkey(id_pubkey)
            )
        )
    else:
        pubkeys = await get_informations_for_identities(id_pubkey)
        if pubkeys == NO_MATCHING_ID:
            print(NO_MATCHING_ID)
        else:
            print("Public keys found matching '{}':\n".format(id_pubkey))
            for pubkey in pubkeys:
                print("→", pubkey["pubkey"], end=" ")
                try:
                    corresponding_id = await client(wot.identity_of, pubkey["pubkey"])
                    print("↔ " + corresponding_id["uid"])
                except:
                    print("")
    await client.close()


async def get_informations_for_identity(id):
    """
    Check that the id is present on the network
    many identities could match
    return the one searched
    """
    certs_req = await get_informations_for_identities(id)
    if certs_req == NO_MATCHING_ID:
        message_exit(NO_MATCHING_ID)
    for certs_id in certs_req:
        if certs_id["uids"][0]["uid"].lower() == id.lower():
            return certs_id
    message_exit(NO_MATCHING_ID)


async def get_uid_from_pubkey(pubkey):
    try:
        client = ClientInstance().client
        lookups = await client(wot.lookup, pubkey)
    except:
        return NO_MATCHING_ID
    for lookup in lookups["results"]:
        if lookup["uids"][0]["uid"] != pubkey:
            return lookup["uids"][0]["uid"]


async def get_informations_for_identities(identifier):
    """
    :identifier: identity or pubkey in part or whole
    Return received and sent certifications lists of matching identities
    if one identity found
    """
    client = ClientInstance().client
    try:
        results = await client(wot.lookup, identifier)
    except:
        return NO_MATCHING_ID
    return results["results"]


async def is_member(pubkey, uid):
    client = ClientInstance().client
    members = await client(wot.members)
    for member in members["results"]:
        if pubkey in member["pubkey"] and uid in member["uid"]:
            return True
    return False


async def get_pubkey_from_id(uid):
    client = ClientInstance().client
    members = await client(wot.members)
    for member in members["results"]:
        if uid == member["uid"]:
            return member["pubkey"]
    return NO_MATCHING_ID
