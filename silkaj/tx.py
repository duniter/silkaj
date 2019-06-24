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
from click import command, option, FloatRange

from tabulate import tabulate
from silkaj.network_tools import ClientInstance, HeadBlock
from silkaj.crypto_tools import check_public_key
from silkaj.tools import message_exit, CurrencySymbol, coroutine
from silkaj.auth import auth_method
from silkaj.wot import is_member
from silkaj.money import (
    get_sources,
    get_amount_from_pubkey,
    UDValue,
    amount_in_current_base,
)
from silkaj.constants import SOURCES_PER_TX

from duniterpy.api.bma.tx import process
from duniterpy.documents import BlockUID, Transaction
from duniterpy.documents.transaction import OutputSource, Unlock, SIGParameter


@command("tx", help="Send transaction")
@option("--amount", type=FloatRange(0.01), help="Quantitative value")
@option("--amountUD", type=float, help="Relative value")
@option("--allSources", is_flag=True, help="Send all sources")
@option(
    "--output",
    required=True,
    help="Pubkey(s)’ recipients + optional checksum: <pubkey>[!checksum]:[<pubkey>[!checksum]]",
)
@option("--comment", default="", help="Comment")
@option(
    "--outputBackChange",
    help="Pubkey recipient to send the rest of the transaction: <pubkey[!checksum]>",
)
@option("--yes", "-y", is_flag=True, help="Assume yes. Do not prompt confirmation")
@coroutine
async def send_transaction(
    amount, amountud, allsources, output, comment, outputbackchange, yes
):
    """
    Main function
    """
    tx_amount = await transaction_amount(amount, amountud, allsources)
    key = auth_method()
    issuer_pubkey = key.pubkey

    pubkey_amount = await get_amount_from_pubkey(issuer_pubkey)
    if allsources:
        tx_amount = pubkey_amount[0]
    outputAddresses = output.split(":")
    check_transaction_values(
        comment,
        outputAddresses,
        outputbackchange,
        pubkey_amount[0] < tx_amount * len(outputAddresses),
        issuer_pubkey,
    )

    if (
        yes
        or input(
            tabulate(
                await transaction_confirmation(
                    issuer_pubkey,
                    pubkey_amount[0],
                    tx_amount,
                    outputAddresses,
                    outputbackchange,
                    comment,
                ),
                tablefmt="fancy_grid",
            )
            + "\nDo you confirm sending this transaction? [yes/no]: "
        )
        == "yes"
    ):
        await handle_intermediaries_transactions(
            key, issuer_pubkey, tx_amount, outputAddresses, comment, outputbackchange
        )


async def transaction_amount(amount, amountUD, allSources):
    """
    Check command line interface amount option
    Return transaction amount
    """
    if not (amount or amountUD or allSources):
        message_exit("--amount nor --amountUD nor --allSources is set")
    if amount:
        return round(amount * 100)
    if amountUD:
        return round(amountUD * await UDValue().ud_value)


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
    issuer_pubkey, pubkey_amount, tx_amount, outputAddresses, outputBackChange, comment
):
    """
    Generate transaction confirmation
    """

    currency_symbol = await CurrencySymbol().symbol
    tx = list()
    tx.append(
        ["pubkey’s balance before tx", str(pubkey_amount / 100) + " " + currency_symbol]
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
            "pubkey’s balance after tx",
            str(((pubkey_amount - tx_amount * len(outputAddresses)) / 100))
            + " "
            + currency_symbol,
        ]
    )
    tx.append(["from (pubkey)", issuer_pubkey])
    id_from = await is_member(issuer_pubkey)
    if id_from:
        tx.append(["from (id)", id_from["uid"]])
    for outputAddress in outputAddresses:
        tx.append(["to (pubkey)", outputAddress])
        id_to = await is_member(outputAddress)
        if id_to:
            tx.append(["to (id)", id_to["uid"]])
    if outputBackChange:
        tx.append(["Backchange (pubkey)", outputBackChange])
        id_backchange = await is_member(outputBackChange)
        if id_backchange:
            tx.append(["Backchange (id)", id_backchange["uid"]])
    tx.append(["comment", comment])
    return tx


async def get_list_input_for_transaction(pubkey, TXamount):
    listinput, amount = await get_sources(pubkey)

    # generate final list source
    listinputfinal = []
    totalAmountInput = 0
    intermediatetransaction = False
    for input in listinput:
        listinputfinal.append(input)
        totalAmountInput += amount_in_current_base(input)
        TXamount -= amount_in_current_base(input)
        # if more than 40 sources, it's an intermediate transaction
        if len(listinputfinal) >= SOURCES_PER_TX:
            intermediatetransaction = True
            break
        if TXamount <= 0:
            break
    if TXamount > 0 and not intermediatetransaction:
        message_exit("Error: you don't have enough money")
    return listinputfinal, totalAmountInput, intermediatetransaction


async def handle_intermediaries_transactions(
    key, issuers, AmountTransfered, outputAddresses, Comment="", OutputbackChange=None
):
    client = ClientInstance().client
    while True:
        listinput_and_amount = await get_list_input_for_transaction(
            issuers, AmountTransfered * len(outputAddresses)
        )
        intermediatetransaction = listinput_and_amount[2]

        if intermediatetransaction:
            totalAmountInput = listinput_and_amount[1]
            await generate_and_send_transaction(
                key,
                issuers,
                totalAmountInput,
                listinput_and_amount,
                issuers,
                "Change operation",
            )
            sleep(1)  # wait 1 second before sending a new transaction

        else:
            await generate_and_send_transaction(
                key,
                issuers,
                AmountTransfered,
                listinput_and_amount,
                outputAddresses,
                Comment,
                OutputbackChange,
            )
            await client.close()
            break


async def generate_and_send_transaction(
    key,
    issuers,
    amount,
    listinput_and_amount,
    outputAddresses,
    Comment,
    OutputbackChange=None,
):
    """
    Display sent transaction
    Generate, sign, and send transaction document
    """
    intermediate_tx = listinput_and_amount[2]
    if intermediate_tx:
        print("Generate Change Transaction")
    else:
        print("Generate Transaction:")
    print("   - From:    " + issuers)
    if isinstance(outputAddresses, str):
        display_sent_tx(outputAddresses, amount)
    else:
        for outputAddress in outputAddresses:
            display_sent_tx(outputAddress, amount)
        if len(outputAddresses) > 1:
            print("   - Total:   " + str(amount / 100 * len(outputAddresses)))

    client = ClientInstance().client
    transaction = await generate_transaction_document(
        issuers,
        amount,
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
        message_exit(
            "Error while publishing transaction: {0}".format(await response.text())
        )


def display_sent_tx(outputAddress, amount):
    print("   - To:     ", outputAddress, "\n   - Amount: ", amount / 100)


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
