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

import urllib
from time import time
from tabulate import tabulate
from duniterpy.api.bma import wot

from silkaj.auth import auth_method
from silkaj.crypto_tools import get_publickey_from_seed, sign_document_from_seed
from silkaj.tools import convert_time, message_exit
from silkaj.network_tools import ClientInstance, post_request, HeadBlock
from silkaj.blockchain_tools import BlockchainParams
from silkaj.license import license_approval
from silkaj.wot import is_member, get_uid_from_pubkey, get_informations_for_identity


async def send_certification(cli_args):
    client = ClientInstance().client
    id_to_certify = await get_informations_for_identity(cli_args.subsubcmd)
    main_id_to_certify = id_to_certify["uids"][0]

    # Display license and ask for confirmation
    head = await HeadBlock().head_block
    license_approval(head["currency"])

    # Authentication
    seed = auth_method(cli_args)

    # Check whether current user is member
    issuer_pubkey = get_publickey_from_seed(seed)
    issuer_id = await get_uid_from_pubkey(issuer_pubkey)
    if not await is_member(issuer_pubkey, issuer_id):
        message_exit("Current identity is not member.")

    if issuer_pubkey == id_to_certify["pubkey"]:
        message_exit("You can’t certify yourself!")

    # Check if the certification can be renewed
    req = await client(wot.requirements, id_to_certify["pubkey"])
    req = req["identities"][0]
    for cert in req["certifications"]:
        if cert["from"] == issuer_pubkey:
            params = await BlockchainParams().params
            # Change params["msWindow"] to params["sigReplay"] when deployed
            # https://git.duniter.org/nodes/typescript/duniter/merge_requests/1270
            # Ğ1: 0<–>2y - 2y + 2m
            # ĞT: 0<–>6m - 6m + ¼m
            renewable = cert["expiresIn"] - params["sigValidity"] + params["msWindow"]
            if renewable > 0:
                renewable_date = convert_time(time() + renewable, "date")
                message_exit("Certification renewable the " + renewable_date)

    # Check if the certification is already in the pending certifications
    for pending_cert in req["pendingCerts"]:
        if pending_cert["from"] == issuer_pubkey:
            message_exit("Certification is currently been processed")

    # Certification confirmation
    if not certification_confirmation(
        issuer_id, issuer_pubkey, id_to_certify, main_id_to_certify
    ):
        await client.close()
        return
    cert_doc = await generate_certification_document(
        issuer_pubkey, id_to_certify, main_id_to_certify
    )
    cert_doc += sign_document_from_seed(cert_doc, seed) + "\n"

    # Send certification document
    post_request("wot/certify", "cert=" + urllib.parse.quote_plus(cert_doc))
    await client.close()
    print("Certification successfully sent.")


def certification_confirmation(
    issuer_id, issuer_pubkey, id_to_certify, main_id_to_certify
):
    cert = list()
    cert.append(["Cert", "From", "–>", "To"])
    cert.append(["ID", issuer_id, "–>", main_id_to_certify["uid"]])
    cert.append(["Pubkey", issuer_pubkey, "–>", id_to_certify["pubkey"]])
    if (
        input(
            tabulate(cert, tablefmt="fancy_grid")
            + "\nDo you confirm sending this certification? [yes/no]: "
        )
        == "yes"
    ):
        return True


async def generate_certification_document(
    issuer_pubkey, id_to_certify, main_id_to_certify
):
    head_block = await HeadBlock().head_block
    return (
        "Version: 10\n\
Type: Certification\n\
Currency: "
        + head_block["currency"]
        + "\n\
Issuer: "
        + issuer_pubkey
        + "\n\
IdtyIssuer: "
        + id_to_certify["pubkey"]
        + "\n\
IdtyUniqueID: "
        + main_id_to_certify["uid"]
        + "\n\
IdtyTimestamp: "
        + main_id_to_certify["meta"]["timestamp"]
        + "\n\
IdtySignature: "
        + main_id_to_certify["self"]
        + "\n\
CertTimestamp: "
        + str(head_block["number"])
        + "-"
        + head_block["hash"]
        + "\n"
    )
