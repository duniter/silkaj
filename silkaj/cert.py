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

from click import command, argument, echo, confirm
from time import time
from tabulate import tabulate
from duniterpy.api.bma import wot, blockchain
from duniterpy.documents import BlockUID, block_uid, Identity, Certification

from silkaj.auth import auth_method
from silkaj.tools import convert_time, message_exit, coroutine
from silkaj.network_tools import ClientInstance, HeadBlock
from silkaj.blockchain_tools import BlockchainParams
from silkaj.license import license_approval
from silkaj.wot import is_member, get_informations_for_identity


@command("cert", help="Send certification")
@argument("id_to_certify")
@coroutine
async def send_certification(id_to_certify):
    client = ClientInstance().client
    id_to_certify = await get_informations_for_identity(id_to_certify)
    main_id_to_certify = id_to_certify["uids"][0]

    # Authentication
    key = auth_method()

    # Check whether current user is member
    issuer_pubkey = key.pubkey
    issuer = await is_member(issuer_pubkey)
    if not issuer:
        message_exit("Current identity is not member.")

    if issuer_pubkey == id_to_certify["pubkey"]:
        message_exit("You can’t certify yourself!")

    # Check if the certification can be renewed
    req = await client(wot.requirements, id_to_certify["pubkey"])
    req = req["identities"][0]
    for cert in req["certifications"]:
        if cert["from"] == issuer_pubkey:
            params = await BlockchainParams().params
            # Ğ1: 0<–>2y - 2y + 2m
            # ĞT: 0<–>4.8m - 4.8m + 12.5d
            renewable = cert["expiresIn"] - params["sigValidity"] + params["sigReplay"]
            if renewable > 0:
                renewable_date = convert_time(time() + renewable, "date")
                message_exit("Certification renewable the " + renewable_date)

    # Check if the certification is already in the pending certifications
    for pending_cert in req["pendingCerts"]:
        if pending_cert["from"] == issuer_pubkey:
            message_exit("Certification is currently been processed")

    # Display license and ask for confirmation
    head = await HeadBlock().head_block
    currency = head["currency"]
    license_approval(currency)

    # Certification confirmation
    await certification_confirmation(
        issuer, issuer_pubkey, id_to_certify, main_id_to_certify
    )

    identity = Identity(
        version=10,
        currency=currency,
        pubkey=id_to_certify["pubkey"],
        uid=main_id_to_certify["uid"],
        ts=block_uid(main_id_to_certify["meta"]["timestamp"]),
        signature=main_id_to_certify["self"],
    )

    certification = Certification(
        version=10,
        currency=currency,
        pubkey_from=issuer_pubkey,
        identity=identity,
        timestamp=BlockUID(head["number"], head["hash"]),
        signature="",
    )

    # Sign document
    certification.sign([key])

    # Send certification document
    response = await client(wot.certify, certification.signed_raw())

    if response.status == 200:
        print("Certification successfully sent.")
    else:
        print("Error while publishing certification: {0}".format(await response.text()))

    await client.close()


async def certification_confirmation(
    issuer, issuer_pubkey, id_to_certify, main_id_to_certify
):
    cert = list()
    cert.append(["Cert", "From", "–>", "To: Published: #block-hash date"])
    client = ClientInstance().client
    idty_timestamp = main_id_to_certify["meta"]["timestamp"]
    block_uid_idty = block_uid(idty_timestamp)
    block = await client(blockchain.block, block_uid_idty.number)
    block_uid_date = (
        ": #" + idty_timestamp[:15] + "… " + convert_time(block["time"], "all")
    )
    cert.append(["ID", issuer["uid"], "–>", main_id_to_certify["uid"] + block_uid_date])
    cert.append(["Pubkey", issuer_pubkey, "–>", id_to_certify["pubkey"]])
    params = await BlockchainParams().params
    cert_begins = convert_time(time(), "date")
    cert_ends = convert_time(time() + params["sigValidity"], "date")
    cert.append(["Valid", cert_begins, "—>", cert_ends])
    echo(tabulate(cert, tablefmt="fancy_grid"))
    confirm("Do you confirm sending this certification?", abort=True)
