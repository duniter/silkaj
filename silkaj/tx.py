from re import compile, search
import math
from time import sleep
import urllib

from tabulate import tabulate
from silkaj.network_tools import get_request, post_request, HeadBlock
from silkaj.crypto_tools import (
    get_publickey_from_seed,
    sign_document_from_seed,
    check_public_key,
)
from silkaj.tools import message_exit, CurrencySymbol
from silkaj.auth import auth_method
from silkaj.wot import get_uid_from_pubkey
from silkaj.money import get_sources, get_amount_from_pubkey, UDValue
from silkaj.constants import NO_MATCHING_ID


def send_transaction(cli_args):
    """
    Main function
    """
    tx_amount, output, comment, allSources, outputBackChange = cmd_transaction(cli_args)
    seed = auth_method(cli_args)
    issuer_pubkey = get_publickey_from_seed(seed)

    pubkey_amount = get_amount_from_pubkey(issuer_pubkey)[0]
    outputAddresses = output.split(":")
    check_transaction_values(
        comment,
        outputAddresses,
        outputBackChange,
        pubkey_amount < tx_amount * len(outputAddresses),
        issuer_pubkey,
    )

    if (
        cli_args.contains_switches("yes")
        or cli_args.contains_switches("y")
        or input(
            tabulate(
                transaction_confirmation(
                    issuer_pubkey, pubkey_amount, tx_amount, outputAddresses, comment
                ),
                tablefmt="fancy_grid",
            )
            + "\nDo you confirm sending this transaction? [yes/no]: "
        )
        == "yes"
    ):
        generate_and_send_transaction(
            seed,
            issuer_pubkey,
            tx_amount,
            outputAddresses,
            comment,
            allSources,
            outputBackChange,
        )


def cmd_transaction(cli_args):
    """
    Retrieve values from command line interface
    """
    if not (
        cli_args.contains_definitions("amount")
        or cli_args.contains_definitions("amountUD")
    ):
        message_exit("--amount or --amountUD is not set")
    if not cli_args.contains_definitions("output"):
        message_exit("--output is not set")

    if cli_args.contains_definitions("amount"):
        tx_amount = float(cli_args.get_definition("amount")) * 100
    if cli_args.contains_definitions("amountUD"):
        tx_amount = float(cli_args.get_definition("amountUD")) * UDValue().ud_value

    output = cli_args.get_definition("output")
    comment = (
        cli_args.get_definition("comment")
        if cli_args.contains_definitions("comment")
        else ""
    )
    allSources = cli_args.contains_switches("allSources")

    if cli_args.contains_definitions("outputBackChange"):
        outputBackChange = cli_args.get_definition("outputBackChange")
    else:
        outputBackChange = None
    return tx_amount, output, comment, allSources, outputBackChange


def check_transaction_values(
    comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey
):
    checkComment(comment)
    for outputAddress in outputAddresses:
        if check_public_key(outputAddress, True) is False:
            message_exit(outputAddress)
    if outputBackChange:
        outputBackChange = check_public_key(outputBackChange, True)
        if check_public_key(outputBackChange, True) is False:
            message_exit(outputBackChange)
    if enough_source:
        message_exit(
            issuer_pubkey + " pubkey doesn’t have enough money for this transaction."
        )


def transaction_confirmation(
    issuer_pubkey, pubkey_amount, tx_amount, outputAddresses, comment
):
    """
    Generate transaction confirmation
    """

    currency_symbol = CurrencySymbol().symbol
    tx = list()
    tx.append(
        ["pubkey’s amount before tx", str(pubkey_amount / 100) + " " + currency_symbol]
    )
    tx.append(
        [
            "tx amount (unit)",
            str(tx_amount / 100 * len(outputAddresses)) + " " + currency_symbol,
        ]
    )
    tx.append(
        [
            "tx amount (relative)",
            str(round(tx_amount / UDValue().ud_value, 4)) + " UD " + currency_symbol,
        ]
    )
    tx.append(
        [
            "pubkey’s amount after tx",
            str(((pubkey_amount - tx_amount * len(outputAddresses)) / 100))
            + " "
            + currency_symbol,
        ]
    )
    tx.append(["from (pubkey)", issuer_pubkey])
    id_from = get_uid_from_pubkey(issuer_pubkey)
    if id_from is not NO_MATCHING_ID:
        tx.append(["from (id)", id_from])
    for outputAddress in outputAddresses:
        tx.append(["to (pubkey)", outputAddress])
        id_to = get_uid_from_pubkey(outputAddress)
        if id_to is not NO_MATCHING_ID:
            tx.append(["to (id)", id_to])
    tx.append(["comment", comment])
    return tx


def generate_and_send_transaction(
    seed,
    issuers,
    AmountTransfered,
    outputAddresses,
    Comment="",
    all_input=False,
    OutputbackChange=None,
):

    while True:
        listinput_and_amount = get_list_input_for_transaction(
            issuers, AmountTransfered * len(outputAddresses), all_input
        )
        intermediatetransaction = listinput_and_amount[2]

        if intermediatetransaction:
            totalAmountInput = listinput_and_amount[1]
            print("Generate Change Transaction")
            print("   - From:    " + issuers)
            print("   - To:      " + issuers)
            print("   - Amount:  " + str(totalAmountInput / 100))
            transaction = generate_transaction_document(
                issuers,
                totalAmountInput,
                listinput_and_amount,
                outputAddresses,
                "Change operation",
            )
            transaction += sign_document_from_seed(transaction, seed) + "\n"
            post_request(
                "tx/process", "transaction=" + urllib.parse.quote_plus(transaction)
            )
            print("Change Transaction successfully sent.")
            sleep(1)  # wait 1 second before sending a new transaction

        else:
            print("Generate Transaction:")
            print("   - From:    " + issuers)
            for outputAddress in outputAddresses:
                print("   - To:      " + outputAddress)
            if all_input:
                print("   - Amount:  " + str(listinput_and_amount[1] / 100))
            else:
                print(
                    "   - Amount:  "
                    + str(AmountTransfered / 100 * len(outputAddresses))
                )
            transaction = generate_transaction_document(
                issuers,
                AmountTransfered,
                listinput_and_amount,
                outputAddresses,
                Comment,
                OutputbackChange,
            )
            transaction += sign_document_from_seed(transaction, seed) + "\n"

            post_request(
                "tx/process", "transaction=" + urllib.parse.quote_plus(transaction)
            )
            print("Transaction successfully sent.")
            break


def generate_transaction_document(
    issuers,
    AmountTransfered,
    listinput_and_amount,
    outputAddresses,
    Comment="",
    OutputbackChange=None,
):

    totalAmountTransfered = AmountTransfered * len(outputAddresses)

    listinput = listinput_and_amount[0]
    totalAmountInput = listinput_and_amount[1]

    head_block = HeadBlock().head_block
    currency_name = head_block["currency"]
    blockstamp_current = str(head_block["number"]) + "-" + str(head_block["hash"])
    curentUnitBase = head_block["unitbase"]

    if not OutputbackChange:
        OutputbackChange = issuers

    # if it's not a foreign exchange transaction, we remove units after 2 digits after the decimal point.
    if issuers not in outputAddresses:
        totalAmountTransfered = (
            totalAmountTransfered // 10 ** curentUnitBase
        ) * 10 ** curentUnitBase

    # Generate output
    ################
    listoutput = []
    # Outputs to receiver (if not himself)
    for outputAddress in outputAddresses:
        rest = AmountTransfered
        unitbase = curentUnitBase
        while rest > 0:
            outputAmount = truncBase(rest, unitbase)
            rest -= outputAmount
            if outputAmount > 0:
                outputAmount = int(outputAmount / math.pow(10, unitbase))
                listoutput.append(
                    str(outputAmount)
                    + ":"
                    + str(unitbase)
                    + ":SIG("
                    + outputAddress
                    + ")"
                )
            unitbase = unitbase - 1

    # Outputs to himself
    unitbase = curentUnitBase
    rest = totalAmountInput - totalAmountTransfered
    while rest > 0:
        outputAmount = truncBase(rest, unitbase)
        rest -= outputAmount
        if outputAmount > 0:
            outputAmount = int(outputAmount / math.pow(10, unitbase))
            listoutput.append(
                str(outputAmount)
                + ":"
                + str(unitbase)
                + ":SIG("
                + OutputbackChange
                + ")"
            )
        unitbase = unitbase - 1

    # Generate transaction document
    ##############################

    transaction_document = "Version: 10\n"
    transaction_document += "Type: Transaction\n"
    transaction_document += "Currency: " + currency_name + "\n"
    transaction_document += "Blockstamp: " + blockstamp_current + "\n"
    transaction_document += "Locktime: 0\n"
    transaction_document += "Issuers:\n"
    transaction_document += issuers + "\n"
    transaction_document += "Inputs:\n"
    for input in listinput:
        transaction_document += input + "\n"
    transaction_document += "Unlocks:\n"
    for i in range(0, len(listinput)):
        transaction_document += str(i) + ":SIG(0)\n"
    transaction_document += "Outputs:\n"
    for output in listoutput:
        transaction_document += output + "\n"
    transaction_document += "Comment: " + Comment + "\n"

    return transaction_document


def get_list_input_for_transaction(pubkey, TXamount, allinput=False):
    listinput, amount = get_sources(pubkey)

    # generate final list source
    listinputfinal = []
    totalAmountInput = 0
    intermediatetransaction = False
    for input in listinput:
        listinputfinal.append(input)
        inputsplit = input.split(":")
        totalAmountInput += int(inputsplit[0]) * 10 ** int(inputsplit[1])
        TXamount -= int(inputsplit[0]) * 10 ** int(inputsplit[1])
        # if more 40 sources, it's an intermediate transaction
        if len(listinputfinal) >= 40:
            intermediatetransaction = True
            break
        if TXamount <= 0 and not allinput:
            break
    if TXamount > 0 and not intermediatetransaction:
        message_exit("Error: you don't have enough money")
    return listinputfinal, totalAmountInput, intermediatetransaction


def checkComment(Comment):
    if len(Comment) > 255:
        message_exit("Error: Comment is too long")
    regex = compile(
        "^[0-9a-zA-Z\ \-\_\:\/\;\*\[\]\(\)\?\!\^\+\=\@\&\~\#\{\}\|\\\<\>\%\.]*$"
    )
    if not search(regex, Comment):
        message_exit("Error: the format of the comment is invalid")


def truncBase(amount, base):
    pow = math.pow(10, base)
    if amount < pow:
        return 0
    return math.trunc(amount / pow) * pow
