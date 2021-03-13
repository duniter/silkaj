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

import sys
import logging

import pendulum
import click
from tabulate import tabulate

from duniterpy.api import bma
from duniterpy.documents import BlockUID, block_uid, Membership

from silkaj import auth, wot, tui
from silkaj.tools import coroutine
from silkaj.network_tools import ClientInstance
from silkaj.blockchain_tools import BlockchainParams, HeadBlock
from silkaj.license import license_approval
from silkaj.constants import SUCCESS_EXIT_STATUS


@click.command(
    "membership",
    help="Send and sign membership document: \n\
for first emission and for renewal",
)
@click.pass_context
@coroutine
async def send_membership(ctx):
    dry_run = ctx.obj["DRY_RUN"]

    # Authentication
    key = auth.auth_method()

    # Get the identity information
    head_block = await HeadBlock().head_block
    membership_timestamp = BlockUID(head_block["number"], head_block["hash"])
    identity = (await wot.choose_identity(key.pubkey))[0]
    identity_uid = identity["uid"]
    identity_timestamp = block_uid(identity["meta"]["timestamp"])

    # Display license and ask for confirmation
    currency = head_block["currency"]
    if not dry_run:
        license_approval(currency)

    # Confirmation
    client = ClientInstance().client
    await display_confirmation_table(identity_uid, key.pubkey, identity_timestamp)
    if not dry_run and not ctx.obj["DISPLAY_DOCUMENT"]:
        await tui.send_doc_confirmation("membership document for this identity")

    membership = generate_membership_document(
        currency,
        key.pubkey,
        membership_timestamp,
        identity_uid,
        identity_timestamp,
    )

    # Sign document
    membership.sign([key])

    logging.debug(membership.signed_raw())

    if dry_run:
        click.echo(membership.signed_raw())
        await client.close()
        sys.exit(SUCCESS_EXIT_STATUS)

    if ctx.obj["DISPLAY_DOCUMENT"]:
        click.echo(membership.signed_raw())
        await tui.send_doc_confirmation("membership document for this identity")

    # Send the membership signed raw document to the node
    response = await client(bma.blockchain.membership, membership.signed_raw())

    if response.status == 200:
        print("Membership successfully sent")
    else:
        print("Error while publishing membership: {0}".format(await response.text()))
    logging.debug(await response.text())
    await client.close()


async def display_confirmation_table(identity_uid, pubkey, identity_timestamp):
    """
    Check whether there is pending memberships already in the mempool
    Display their expiration date

    Actually, it works sending a membership document even if the time
    between two renewals is not awaited as for the certification
    """

    client = ClientInstance().client

    identities_requirements = await client(bma.wot.requirements, pubkey)
    for identity_requirements in identities_requirements["identities"]:
        if identity_requirements["uid"] == identity_uid:
            membership_expires = identity_requirements["membershipExpiresIn"]
            pending_expires = identity_requirements["membershipPendingExpiresIn"]
            pending_memberships = identity_requirements["pendingMemberships"]
            break

    table = list()
    if membership_expires:
        expires = pendulum.now().add(seconds=membership_expires).diff_for_humans()
        table.append(["Expiration date of current membership", expires])

    if pending_memberships:
        line = [
            "Number of pending membership(s) in the mempool",
            len(pending_memberships),
        ]
        table.append(line)

        expiration = pendulum.now().add(seconds=pending_expires).diff_for_humans()
        table.append(["Pending membership documents will expire", expiration])

    table.append(["User Identifier (UID)", identity_uid])
    table.append(["Public Key", tui.display_pubkey_and_checksum(pubkey)])

    table.append(["Block Identity", str(identity_timestamp)[:45] + "…"])

    block = await client(bma.blockchain.block, identity_timestamp.number)
    table.append(
        ["Identity published", pendulum.from_timestamp(block["time"]).format("LL")]
    )

    params = await BlockchainParams().params
    membership_validity = (
        pendulum.now().add(seconds=params["msValidity"]).diff_for_humans()
    )
    table.append(["Expiration date of new membership", membership_validity])

    membership_mempool = (
        pendulum.now().add(seconds=params["msPeriod"]).diff_for_humans()
    )
    table.append(
        ["Expiration date of new membership from the mempool", membership_mempool]
    )

    click.echo(tabulate(table, tablefmt="fancy_grid"))


def generate_membership_document(
    currency,
    pubkey,
    membership_timestamp,
    identity_uid,
    identity_timestamp,
):
    return Membership(
        version=10,
        currency=currency,
        issuer=pubkey,
        membership_ts=membership_timestamp,
        membership_type="IN",
        uid=identity_uid,
        identity_ts=identity_timestamp,
    )
