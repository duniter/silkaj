import urllib
from tabulate import tabulate

from silkaj.auth import auth_method
from silkaj.crypto_tools import get_publickey_from_seed, sign_document_from_seed
from silkaj.tools import message_exit
from silkaj.network_tools import post_request, HeadBlock
from silkaj.license import license_approval
from silkaj.wot import is_member, get_uid_from_pubkey, get_informations_for_identity


def send_certification(cli_args):
    id_to_certify = get_informations_for_identity(cli_args.subsubcmd)
    main_id_to_certify = id_to_certify["uids"][0]

    # Display license and ask for confirmation
    license_approval(HeadBlock().head_block["currency"])

    # Authentication
    seed = auth_method(cli_args)

    # Check whether current user is member
    issuer_pubkey = get_publickey_from_seed(seed)
    issuer_id = get_uid_from_pubkey(issuer_pubkey)
    if not is_member(issuer_pubkey, issuer_id):
        message_exit("Current identity is not member.")

    if issuer_pubkey == id_to_certify["pubkey"]:
        message_exit("You can’t certify yourself!")

    for certifier in main_id_to_certify["others"]:
        if certifier["pubkey"] == issuer_pubkey:
            message_exit("Identity already certified by " + issuer_id)

    # Certification confirmation
    if not certification_confirmation(
        issuer_id, issuer_pubkey, id_to_certify, main_id_to_certify
    ):
        return
    cert_doc = generate_certification_document(
        issuer_pubkey, id_to_certify, main_id_to_certify
    )
    cert_doc += sign_document_from_seed(cert_doc, seed) + "\n"

    # Send certification document
    post_request("wot/certify", "cert=" + urllib.parse.quote_plus(cert_doc))
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


def generate_certification_document(issuer_pubkey, id_to_certify, main_id_to_certify):
    head_block = HeadBlock().head_block
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
