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

import click
from time import time
from tabulate import tabulate
from collections import OrderedDict
from asyncio import sleep
from duniterpy.api.bma import wot, blockchain
from duniterpy.api.errors import DuniterError

from silkaj.network_tools import ClientInstance
from silkaj.crypto_tools import is_pubkey_and_check
from silkaj.tools import message_exit, coroutine
from silkaj.tui import convert_time, display_pubkey_and_checksum
from silkaj.blockchain_tools import BlockchainParams
from silkaj.constants import ASYNC_SLEEP


def get_sent_certifications(signed, time_first_block, params):
    sent = list()
    expire = list()
    if signed:
        for cert in signed:
            sent.append(cert["uid"])
            expire.append(
                expiration_date_from_block_id(
                    cert["cert_time"]["block"], time_first_block, params
                )
            )
    return sent, expire


@click.command(
    "wot",
    help="Check received and sent certifications and consult the membership status of any given identity",
)
@click.argument("uid_pubkey")
@coroutine
async def received_sent_certifications(uid_pubkey):
    """
    get searched id
    get id of received and sent certifications
    display in a table the result with the numbers
    """
    client = ClientInstance().client
    first_block = await client(blockchain.block, 1)
    time_first_block = first_block["time"]

    checked_pubkey = is_pubkey_and_check(uid_pubkey)
    if checked_pubkey:
        uid_pubkey = checked_pubkey

    identity, pubkey, signed = await choose_identity(uid_pubkey)
    certifications = OrderedDict()
    params = await BlockchainParams().params
    req = await client(wot.requirements, pubkey)
    req = req["identities"][0]
    certifications["received_expire"] = list()
    certifications["received"] = list()
    for cert in identity["others"]:
        certifications["received_expire"].append(
            expiration_date_from_block_id(
                cert["meta"]["block_number"], time_first_block, params
            )
        )
        certifications["received"].append(
            cert_written_in_the_blockchain(req["certifications"], cert)
        )
        (
            certifications["sent"],
            certifications["sent_expire"],
        ) = get_sent_certifications(signed, time_first_block, params)
    nbr_sent_certs = len(certifications["sent"]) if "sent" in certifications else 0
    print(
        "{0} ({1}) from block #{2}\nreceived {3} and sent {4}/{5} certifications:\n{6}\n{7}\n".format(
            identity["uid"],
            display_pubkey_and_checksum(pubkey, True),
            identity["meta"]["timestamp"][:15] + "…",
            len(certifications["received"]),
            nbr_sent_certs,
            params["sigStock"],
            tabulate(
                certifications,
                headers="keys",
                tablefmt="orgtbl",
                stralign="center",
            ),
            "✔: Certification available to be written or already written into the blockchain",
        )
    )
    await membership_status(certifications, pubkey, req)
    await client.close()


def cert_written_in_the_blockchain(written_certs, certifieur):
    for cert in written_certs:
        if cert["from"] == certifieur["pubkey"]:
            return certifieur["uids"][0] + " ✔"
    return certifieur["uids"][0]


async def membership_status(certifications, pubkey, req):
    params = await BlockchainParams().params
    if len(certifications["received"]) >= params["sigQty"]:
        print(
            "Membership expiration due to certification expirations: "
            + certifications["received_expire"][
                len(certifications["received"]) - params["sigQty"]
            ]
        )
    member = await is_member(pubkey)
    if member:
        member = True
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


@click.command("lookup", help="User identifier and public key lookup")
@click.argument("uid_pubkey")
@coroutine
async def id_pubkey_correspondence(uid_pubkey):
    checked_pubkey = is_pubkey_and_check(uid_pubkey)
    if checked_pubkey:
        uid_pubkey = checked_pubkey

    client = ClientInstance().client
    lookups = await wot_lookup(uid_pubkey)
    await client.close()

    content = f"Public keys or user id found matching '{uid_pubkey}':\n"
    for lookup in lookups:
        for identity in lookup["uids"]:
            pubkey_checksum = display_pubkey_and_checksum(lookup["pubkey"])
            content += f'\n→ {pubkey_checksum} ↔ {identity["uid"]}'
    click.echo(content)


async def choose_identity(pubkey_uid):
    """
    Get lookup from a pubkey or an uid
    Loop over the double lists: pubkeys, then uids
    If there is one uid, returns it
    If there is multiple uids, prompt a selector
    """
    lookups = await wot_lookup(pubkey_uid)

    # Generate table containing the choices
    identities_choices = {"id": [], "uid": [], "pubkey": [], "timestamp": []}
    for pubkey_index, lookup in enumerate(lookups):
        for uid_index, identity in enumerate(lookup["uids"]):
            identities_choices["id"].append(str(pubkey_index) + str(uid_index))
            identities_choices["pubkey"].append(
                display_pubkey_and_checksum(lookup["pubkey"])
            )
            identities_choices["uid"].append(identity["uid"])
            identities_choices["timestamp"].append(
                identity["meta"]["timestamp"][:20] + "…"
            )

    identities = len(identities_choices["uid"])
    if identities == 1:
        pubkey_index = 0
        uid_index = 0
    elif identities > 1:
        table = tabulate(identities_choices, headers="keys", tablefmt="orgtbl")
        click.echo(table)

        # Loop till the passed value is in identities_choices
        message = "Which identity would you like to select (id)?"
        selected_id = None
        while selected_id not in identities_choices["id"]:
            selected_id = click.prompt(message)

        pubkey_index = int(selected_id[:-1])
        uid_index = int(selected_id[-1:])

    return (
        lookups[pubkey_index]["uids"][uid_index],
        lookups[pubkey_index]["pubkey"],
        lookups[pubkey_index]["signed"],
    )


async def identity_of(pubkey_uid):
    """
    Only works for members
    Not able to get corresponding uid from a non-member identity
    Able to know if an identity is member or not
    """
    client = ClientInstance().client
    try:
        return await client(wot.identity_of, pubkey_uid)
    except ValueError as e:
        pass


async def is_member(pubkey_uid):
    """
    Check identity is member
    If member, return corresponding identity, else: False
    """
    try:
        return await identity_of(pubkey_uid)
    except:
        return False


async def wot_lookup(identifier):
    """
    :identifier: identity or pubkey in part or whole
    Return received and sent certifications lists of matching identities
    if one identity found
    """
    client = ClientInstance().client
    try:
        results = await client(wot.lookup, identifier)
        return results["results"]
    except DuniterError as e:
        message_exit(e.message)
    except ValueError as e:
        pass


async def identities_from_pubkeys(pubkeys, uids):
    """
    Make list of pubkeys unique, and remove empty strings
    Request identities
    """
    if not uids:
        return list()

    uniq_pubkeys = list(filter(None, set(pubkeys)))
    identities = list()
    for pubkey in uniq_pubkeys:
        try:
            identities.append(await identity_of(pubkey))
        except Exception as e:
            pass
        await sleep(ASYNC_SLEEP)
    return identities
