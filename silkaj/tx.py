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

from re import compile, search
import math
from time import sleep

from tabulate import tabulate
from silkaj.network_tools import ClientInstance, HeadBlock
from silkaj.crypto_tools import check_public_key
from silkaj.tools import message_exit, CurrencySymbol
from silkaj.auth import auth_method
from silkaj.wot import get_uid_from_pubkey
from silkaj.money import get_sources, get_amount_from_pubkey, UDValue
from silkaj.constants import NO_MATCHING_ID

from duniterpy.api.bma.tx import process
from duniterpy.documents import BlockUID, Transaction
from duniterpy.documents.transaction import OutputSource, Unlock, SIGParameter


async def send_transaction(cli_args):
    """
    Main function
    """
    tx_amount, output, comment, allSources, outputBackChange = await cmd_transaction(
        cli_args
    )
    key = auth_method(cli_args)
    issuer_pubkey = key.pubkey

    pubkey_amount = await get_amount_from_pubkey(issuer_pubkey)
    outputAddresses = output.split(":")
    check_transaction_values(
        comment,
        outputAddresses,
        outputBackChange,
        pubkey_amount[0] < tx_amount * len(outputAddresses),
        issuer_pubkey,
    )

    if (
        cli_args.contains_switches("yes")
        or cli_args.contains_switches("y")
        or input(
            tabulate(
                await transaction_confirmation(
                    issuer_pubkey, pubkey_amount[0], tx_amount, outputAddresses, comment
                ),
                tablefmt="fancy_grid",
            )
            + "\nDo you confirm sending this transaction? [yes/no]: "
        )
        == "yes"
    ):
        await generate_and_send_transaction(
            key,
            issuer_pubkey,
            tx_amount,
            outputAddresses,
            comment,
            allSources,
            outputBackChange,
        )


async def cmd_transaction(cli_args):
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
        tx_amount = (
            float(cli_args.get_definition("amountUD")) * await UDValue().ud_value
        )

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


async def transaction_confirmation(
    issuer_pubkey, pubkey_amount, tx_amount, outputAddresses, comment
):
    """
    Generate transaction confirmation
    """

    currency_symbol = await CurrencySymbol().symbol
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
            str(round(tx_amount / await UDValue().ud_value, 4))
            + " UD "
            + currency_symbol,
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
    id_from = await get_uid_from_pubkey(issuer_pubkey)
    if id_from is not NO_MATCHING_ID:
        tx.append(["from (id)", id_from])
    for outputAddress in outputAddresses:
        tx.append(["to (pubkey)", outputAddress])
        id_to = await get_uid_from_pubkey(outputAddress)
        if id_to is not NO_MATCHING_ID:
            tx.append(["to (id)", id_to])
    tx.append(["comment", comment])
    return tx


async def generate_and_send_transaction(
    key,
    issuers,
    AmountTransfered,
    outputAddresses,
    Comment="",
    all_input=False,
    OutputbackChange=None,
):

    client = ClientInstance().client
    while True:
        listinput_and_amount = await get_list_input_for_transaction(
            issuers, AmountTransfered * len(outputAddresses), all_input
        )
        intermediatetransaction = listinput_and_amount[2]

        if intermediatetransaction:
            totalAmountInput = listinput_and_amount[1]
            print("Generate Change Transaction")
            print("   - From:    " + issuers)
            print("   - To:      " + issuers)
            print("   - Amount:  " + str(totalAmountInput / 100))
            transaction = await generate_transaction_document(
                issuers,
                totalAmountInput,
                listinput_and_amount,
                issuers,
                "Change operation",
            )
            transaction.sign([key])
            response = await client(process, transaction.signed_raw())
            if response.status == 200:
                print("Change Transaction successfully sent.")
            else:
                print(
                    "Error while publishing transaction: {0}".format(
                        await response.text()
                    )
                )

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
            transaction = await generate_transaction_document(
                issuers,
                AmountTransfered,
                listinput_and_amount,
                outputAddresses,
                Comment,
                OutputbackChange,
            )
            transaction.sign([key])
            response = await client(process, transaction.signed_raw())
            if response.status == 200:
                print("Transaction successfully sent.")
            else:
                print(
                    "Error while publishing transaction: {0}".format(
                        await response.text()
                    )
                )

            await client.close()
            break


async def generate_transaction_document(
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

    head_block = await HeadBlock().head_block
    currency_name = head_block["currency"]
    blockstamp_current = BlockUID(head_block["number"], head_block["hash"])
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
    if isinstance(outputAddresses, str):
        generate_output(listoutput, curentUnitBase, AmountTransfered, outputAddresses)
    else:
        for outputAddress in outputAddresses:
            generate_output(listoutput, curentUnitBase, AmountTransfered, outputAddress)

    # Outputs to himself
    rest = totalAmountInput - totalAmountTransfered
    generate_output(listoutput, curentUnitBase, rest, OutputbackChange)

    # Unlocks
    unlocks = generate_unlocks(listinput)

    # Generate transaction document
    ##############################

    return Transaction(
        version=10,
        currency=currency_name,
        blockstamp=blockstamp_current,
        locktime=0,
        issuers=[issuers],
        inputs=listinput,
        unlocks=unlocks,
        outputs=listoutput,
        comment=Comment,
        signatures=[],
    )


def generate_unlocks(listinput):
    unlocks = list()
    for i in range(0, len(listinput)):
        unlocks.append(Unlock(index=i, parameters=[SIGParameter(0)]))
    return unlocks


def generate_output(listoutput, unitbase, rest, recipient_address):
    while rest > 0:
        outputAmount = truncBase(rest, unitbase)
        rest -= outputAmount
        if outputAmount > 0:
            outputAmount = int(outputAmount / math.pow(10, unitbase))
            listoutput.append(
                OutputSource(
                    amount=str(outputAmount),
                    base=unitbase,
                    condition="SIG({0})".format(recipient_address),
                )
            )
        unitbase = unitbase - 1


async def get_list_input_for_transaction(pubkey, TXamount, allinput=False):
    listinput, amount = await get_sources(pubkey)

    # generate final list source
    listinputfinal = []
    totalAmountInput = 0
    intermediatetransaction = False
    for input in listinput:
        listinputfinal.append(input)
        totalAmountInput += input.amount * 10 ** input.base
        TXamount -= input.amount * 10 ** input.base
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
