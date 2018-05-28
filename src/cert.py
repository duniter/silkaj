import webbrowser
import urllib

from sys import exit
from pydoc import pager
from tabulate import tabulate

from auth import auth_method
from tools import get_publickey_from_seed, message_exit, sign_document_from_seed
from network_tools import get_current_block, post_request
from constants import NO_MATCHING_ID
from wot import is_member, get_pubkey_from_id, get_pubkeys_from_id,\
        get_uid_from_pubkey


def send_certification(ep, cli_args):
    current_blk = get_current_block(ep)
    certified_uid = cli_args.subsubcmd
    certified_pubkey = get_pubkey_from_id(ep, certified_uid)

    # Check that the id is present on the network
    if (certified_pubkey is NO_MATCHING_ID):
        message_exit(NO_MATCHING_ID)

    # Display license and ask for confirmation
    license_approval(current_blk["currency"])

    # Authentication
    seed = auth_method(cli_args)

    # Check whether current user is member
    issuer_pubkey = get_publickey_from_seed(seed)
    issuer_id = get_uid_from_pubkey(ep, issuer_pubkey)
    if not is_member(ep, issuer_pubkey, issuer_id):
        message_exit("Current identity is not member.")

    # Check whether issuer and certified identities are different
    if issuer_pubkey == certified_pubkey:
        message_exit("You can’t certify yourself!")

    # Check if this certification is already present on the network
    id_lookup = get_pubkeys_from_id(ep, certified_uid)[0]
    for certifiers in id_lookup["uids"][0]["others"]:
        if certifiers["pubkey"] == issuer_pubkey:
            message_exit("Identity already certified by " + issuer_id)

    # Certification confirmation
    if not certification_confirmation(issuer_id, issuer_pubkey, certified_uid, certified_pubkey):
        return
    cert_doc = generate_certification_document(id_lookup, current_blk, issuer_pubkey, certified_uid)
    cert_doc += sign_document_from_seed(cert_doc, seed) + "\n"

    # Send certification document
    post_request(ep, "wot/certify", "cert=" + urllib.parse.quote_plus(cert_doc))
    print("Certification successfully sent.")


def license_approval(currency):
    if currency != "g1":
        return
    language = input("In which language would you like to display Ğ1 license [en/fr]? ")
    if (language == "en"):
        if not webbrowser.open("https://duniter.org/en/get-g1/"):
            pager(open("licence-G1/license/license_g1-en.rst").read())
    else:
        if not webbrowser.open("https://duniter.org/fr/wiki/licence-g1/"):
            pager(open("licence-G1/license/license_g1-fr-FR.rst").read())

    if (input("Do you approve Ğ1 license [yes/no]? ") != "yes"):
        exit(1)


def certification_confirmation(issuer_id, issuer_pubkey, certified_uid, certified_pubkey):
    cert = list()
    cert.append(["Cert", "From", "–>", "To"])
    cert.append(["ID", issuer_id, "–>", certified_uid])
    cert.append(["Pubkey", issuer_pubkey, "–>", certified_pubkey])
    if input(tabulate(cert, tablefmt="fancy_grid") +
       "\nDo you confirm sending this certification? [yes/no]: ") == "yes":
        return True


def generate_certification_document(id_lookup, current_blk, issuer_pubkey, certified_uid):
    return "Version: 10\n\
Type: Certification\n\
Currency: " + current_blk["currency"] + "\n\
Issuer: " + issuer_pubkey + "\n\
IdtyIssuer: " + id_lookup["pubkey"] + "\n\
IdtyUniqueID: " + certified_uid + "\n\
IdtyTimestamp: " + id_lookup["uids"][0]["meta"]["timestamp"] + "\n\
IdtySignature: " + id_lookup["uids"][0]["self"] + "\n\
CertTimestamp: " + str(current_blk["number"]) + "-" + current_blk["hash"] + "\n"
