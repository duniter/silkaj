from re import compile, search
import math
from time import sleep
from sys import exit
import urllib

from tabulate import tabulate
from network_tools import get_request, post_request, get_current_block
from tools import get_currency_symbol, get_publickey_from_seed, sign_document_from_seed,\
        check_public_key, message_exit
from auth import auth_method
from wot import get_uid_from_pubkey
from money import get_last_ud_value, get_amount_from_pubkey
from constants import NO_MATCHING_ID


def send_transaction(ep, cli_args):
    """
    Main function
    """
    ud = get_last_ud_value(ep)
    amount, output, comment, allSources, outputBackChange = cmd_transaction(cli_args, ud)
    check_transaction_values(comment, output, outputBackChange)
    seed = auth_method(cli_args)
    issuer_pubkey = get_publickey_from_seed(seed)

    if cli_args.contains_switches('yes') or cli_args.contains_switches('y') or \
        input(tabulate(transaction_confirmation(ep, issuer_pubkey, amount, ud, output, comment),
        tablefmt="fancy_grid") + "\nDo you confirm sending this transaction? [yes/no]: ") == "yes":
        generate_and_send_transaction(ep, seed, issuer_pubkey, amount, output, comment, allSources, outputBackChange)


def cmd_transaction(cli_args, ud):
    """
    Retrieve values from command line interface
    """
    if not (cli_args.contains_definitions('amount') or cli_args.contains_definitions('amountUD')):
        message_exit("--amount or --amountUD is not set")
    if not cli_args.contains_definitions('output'):
        message_exit("--output is not set")

    if cli_args.contains_definitions('amount'):
        amount = int(float(cli_args.get_definition('amount')) * 100)
    if cli_args.contains_definitions('amountUD'):
        amount = int(float(cli_args.get_definition('amountUD')) * ud)

    output = cli_args.get_definition('output')
    comment = cli_args.get_definition('comment') if cli_args.contains_definitions('comment') else ""
    allSources = cli_args.contains_switches('allSources')

    if cli_args.contains_definitions('outputBackChange'):
        outputBackChange = cli_args.get_definition('outputBackChange')
    else:
        outputBackChange = None
    return amount, output, comment, allSources, outputBackChange


def check_transaction_values(comment, output, outputBackChange):
    checkComment(comment)

    output = check_public_key(output, True)
    if outputBackChange:
        outputBackChange = check_public_key(outputBackChange, True)
    if output is False or outputBackChange is False:
        exit(1)


def transaction_confirmation(ep, issuer_pubkey, amount, ud, output, comment):
    """
    Generate transaction confirmation
    """
    tx = list()
    currency_symbol = get_currency_symbol(get_current_block(ep)["currency"])
    tx.append(["amount (" + currency_symbol + ")", amount / 100])
    tx.append(["amount (UD " + currency_symbol + ")", amount / ud])
    tx.append(["from", issuer_pubkey])
    id_from = get_uid_from_pubkey(ep, issuer_pubkey)
    if id_from is not NO_MATCHING_ID:
        tx.append(["from (id)", id_from])
    tx.append(["to", output])
    id_to = get_uid_from_pubkey(ep, output)
    if id_to is not NO_MATCHING_ID:
        tx.append(["to (id)", id_to])
    tx.append(["comment", comment])
    return tx


def generate_and_send_transaction(ep, seed, issuers, AmountTransfered, outputAddr, Comment="", all_input=False, OutputbackChange=None):
    totalamount = get_amount_from_pubkey(ep, issuers)[0]
    if totalamount < AmountTransfered:
        message_exit("the account: " + issuers + " don't have enough money for this transaction")

    while True:
        listinput_and_amount = get_list_input_for_transaction(ep, issuers, AmountTransfered, all_input)
        intermediatetransaction = listinput_and_amount[2]

        if intermediatetransaction:
            totalAmountInput = listinput_and_amount[1]
            print("Generate Change Transaction")
            print("   - From:    " + issuers)
            print("   - To:      " + issuers)
            print("   - Amount:  " + str(totalAmountInput / 100))
            transaction = generate_transaction_document(ep, issuers, totalAmountInput, listinput_and_amount, issuers, "Change operation")
            transaction += sign_document_from_seed(transaction, seed) + "\n"
            post_request(ep, "tx/process", "transaction=" + urllib.parse.quote_plus(transaction))
            print("Change Transaction successfully sent.")
            sleep(1)  # wait 1 second before sending a new transaction

        else:
            print("Generate Transaction:")
            print("   - From:    " + issuers)
            print("   - To:      " + outputAddr)
            if all_input:
                print("   - Amount:  " + str(listinput_and_amount[1] / 100))
            else:
                print("   - Amount:  " + str(AmountTransfered / 100))
            transaction = generate_transaction_document(ep, issuers, AmountTransfered, listinput_and_amount, outputAddr, Comment, OutputbackChange)
            transaction += sign_document_from_seed(transaction, seed) + "\n"

            post_request(ep, "tx/process", "transaction=" + urllib.parse.quote_plus(transaction))
            print("Transaction successfully sent.")
            break


def generate_transaction_document(ep, issuers, AmountTransfered, listinput_and_amount, outputaddr, Comment="", OutputbackChange=None):
    check_public_key(outputaddr, True)
    if OutputbackChange:
        OutputbackChange = check_public_key(OutputbackChange, True)

    listinput = listinput_and_amount[0]
    totalAmountInput = listinput_and_amount[1]

    current_blk = get_current_block(ep)
    currency_name = current_blk["currency"]
    blockstamp_current = str(current_blk["number"]) + "-" + str(current_blk["hash"])
    curentUnitBase = current_blk["unitbase"]

    if not OutputbackChange:
        OutputbackChange = issuers

    # if it's not a foreign exchange transaction, we remove units after 2 digits after the decimal point.
    if issuers != outputaddr:
        AmountTransfered = (AmountTransfered // 10 ** curentUnitBase) * 10 ** curentUnitBase

    # Generate output
    ################
    listoutput = []
    # Outputs to receiver (if not himself)
    rest = AmountTransfered
    unitbase = curentUnitBase
    while rest > 0:
        outputAmount = truncBase(rest, unitbase)
        rest -= outputAmount
        if outputAmount > 0:
            outputAmount = int(outputAmount / math.pow(10, unitbase))
            listoutput.append(str(outputAmount) + ":" + str(unitbase) + ":SIG(" + outputaddr + ")")
        unitbase = unitbase - 1

    # Outputs to himself
    unitbase = curentUnitBase
    rest = totalAmountInput - AmountTransfered
    while rest > 0:
        outputAmount = truncBase(rest, unitbase)
        rest -= outputAmount
        if outputAmount > 0:
            outputAmount = int(outputAmount / math.pow(10, unitbase))
            listoutput.append(str(outputAmount) + ":" + str(unitbase) + ":SIG(" + OutputbackChange + ")")
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


def get_list_input_for_transaction(ep, pubkey, TXamount, allinput=False):
    # real source in blockchain
    sources = get_request(ep, "tx/sources/" + pubkey)["sources"]
    if sources is None:
        return None
    listinput = []

    for source in sources:
        if source["conditions"] == "SIG(" + pubkey + ")":
            listinput.append(str(source["amount"]) + ":" + str(source["base"]) + ":" + str(source["type"]) + ":" + str(source["identifier"]) + ":" + str(source["noffset"]))

    # pending source
    history = get_request(ep, "tx/history/" + pubkey + "/pending")["history"]
    pendings = history["sending"] + history["receiving"] + history["pending"]

    current_blk = get_current_block(ep)
    last_block_number = int(current_blk["number"])

    # add pending output
    for pending in pendings:
        blockstamp = pending["blockstamp"]
        block_number = int(blockstamp.split("-")[0])
        # if it's not an old transaction (bug in mirror node)
        if block_number >= last_block_number - 3:
            identifier = pending["hash"]
            i = 0
            for output in pending["outputs"]:
                outputsplited = output.split(":")
                if outputsplited[2] == "SIG("+pubkey+")":
                    inputgenerated = str(outputsplited[0]) + ":" + str(outputsplited[1]) + ":T:" + identifier + ":" + str(i)
                    if inputgenerated not in listinput:
                        listinput.append(inputgenerated)
                i += 1

    # remove input already used
    for pending in pendings:
        blockstamp = pending["blockstamp"]
        block_number = int(blockstamp.split("-")[0])
        # if it's not an old transaction (bug in mirror node)
        if block_number >= last_block_number - 3:
            for input in pending["inputs"]:
                if input in listinput:
                    listinput.remove(input)

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
    regex = compile('^[0-9a-zA-Z\ \-\_\:\/\;\*\[\]\(\)\?\!\^\+\=\@\&\~\#\{\}\|\\\<\>\%\.]*$')
    if not search(regex, Comment):
        message_exit("Error: the format of the comment is invalid")


def truncBase(amount, base):
    pow = math.pow(10, base)
    if amount < pow:
        return 0
    return math.trunc(amount / pow) * pow
