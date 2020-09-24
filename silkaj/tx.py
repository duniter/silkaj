"""
Copyright  2016-2020 Maël Azimi <m.a@moul.re>

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
from asyncio import sleep
from tabulate import tabulate
from click import command, option, FloatRange

from silkaj.cli_tools import MutuallyExclusiveOption
from silkaj.network_tools import ClientInstance
from silkaj.blockchain_tools import HeadBlock
from silkaj.crypto_tools import validate_checksum, check_pubkey_format
from silkaj.tools import message_exit, CurrencySymbol, coroutine
from silkaj.auth import auth_method
from silkaj import money
from silkaj.constants import (
    SOURCES_PER_TX,
    MINIMAL_TX_AMOUNT,
    CENT_MULT_TO_UNIT,
    ASYNC_SLEEP,
)
from silkaj.tui import display_amount, display_pubkey, display_pubkey_and_checksum

from duniterpy.api.bma.tx import process
from duniterpy.documents import BlockUID, Transaction
from duniterpy.documents.transaction import OutputSource, Unlock, SIGParameter


@command("tx", help="Send transaction")
@option(
    "amounts",
    "--amount",
    "-a",
    multiple=True,
    type=FloatRange(MINIMAL_TX_AMOUNT),
    help="Quantitative amount(s):\n-a <amount>\nMinimum amount is {0}".format(
        MINIMAL_TX_AMOUNT
    ),
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["amountsud", "allsources"],
)
@option(
    "amountsud",
    "--amountUD",
    "-d",
    multiple=True,
    type=float,
    help="Relative amount(s):\n-d <amount_UD>",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["amounts", "allsources"],
)
@option(
    "--allSources",
    is_flag=True,
    help="Send all sources to one recipient",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["amounts", "amountsud"],
)
@option(
    "recipients",
    "--recipient",
    "-r",
    multiple=True,
    required=True,
    help="Pubkey(s)’ recipients + optional checksum:\n-r <pubkey>[:checksum]\n\
Sending to many recipients is possible:\n\
* With one amount, all will receive the amount\n\
* With many amounts (one per recipient)",
)
@option("--comment", "-c", default="", help="Comment")
@option(
    "--outputBackChange",
    help="Pubkey recipient to send the rest of the transaction: <pubkey[:checksum]>",
)
@option("--yes", "-y", is_flag=True, help="Assume yes. Do not prompt confirmation")
@coroutine
async def send_transaction(
    amounts, amountsud, allsources, recipients, comment, outputbackchange, yes
):
    """
    Main function
    """
    if not (amounts or amountsud or allsources):
        message_exit("Error: amount, amountUD or allSources is not set.")
    if allsources and len(recipients) > 1:
        message_exit(
            "Error: the --allSources option can only be used with one recipient."
        )
    # compute amounts and amountsud
    if not allsources:
        tx_amounts = await transaction_amount(amounts, amountsud, recipients)

    key = auth_method()
    issuer_pubkey = key.pubkey

    pubkey_amount = await money.get_amount_from_pubkey(issuer_pubkey)
    if allsources:
        tx_amounts = [pubkey_amount[0]]

    recipients = list(recipients)
    outputbackchange = check_transaction_values(
        comment,
        recipients,
        outputbackchange,
        pubkey_amount[0] < sum(tx_amounts),
        issuer_pubkey,
    )

    if (
        yes
        or input(
            tabulate(
                await transaction_confirmation(
                    issuer_pubkey,
                    pubkey_amount[0],
                    tx_amounts,
                    recipients,
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
            key,
            issuer_pubkey,
            tx_amounts,
            recipients,
            comment,
            outputbackchange,
        )
    else:
        client = ClientInstance().client
        await client.close()


async def transaction_amount(amounts, UDs_amounts, outputAddresses):
    """
    Check that the number of passed amounts(UD) and recipients are the same
    Returns a list of amounts.
    """
    # Create amounts list
    if amounts:
        amounts_list = compute_amounts(amounts, CENT_MULT_TO_UNIT)
    elif UDs_amounts:
        UD_value = await money.UDValue().ud_value
        amounts_list = compute_amounts(UDs_amounts, UD_value)
    if len(amounts_list) != len(outputAddresses) and len(amounts_list) != 1:
        message_exit(
            "Error: The number of passed recipients is not the same as the passed amounts."
        )
    # In case one amount is passed with multiple recipients
    # generate list containing multiple time the same amount
    if len(amounts_list) == 1 and len(outputAddresses) > 1:
        amounts_list = [amounts_list[0]] * len(outputAddresses)
    return amounts_list


def compute_amounts(amounts, multiplicator):
    """
    Computes the amounts(UD) and returns a list.
    Multiplicator should be either CENT_MULT_TO_UNIT or UD_Value.
    If relative amount, check that amount is superior to minimal amount.
    """
    # Create amounts list
    amounts_list = list()
    for amount in amounts:
        computed_amount = amount * multiplicator
        # check if relative amounts are high enough
        if (multiplicator != CENT_MULT_TO_UNIT) and (
            computed_amount < (MINIMAL_TX_AMOUNT * CENT_MULT_TO_UNIT)
        ):
            message_exit("Error: amount {0} is too low.".format(amount))
        amounts_list.append(round(computed_amount))
    return amounts_list


def check_transaction_values(
    comment, outputAddresses, outputBackChange, enough_source, issuer_pubkey
):
    """
    Check the comment format
    Check the pubkeys and the checksums of the recipients and the outputbackchange
    In case of a valid checksum, assign and return the pubkey without the checksum
    Check the balance is big enough for the transaction
    """
    checkComment(comment)
    for i, outputAddress in enumerate(outputAddresses):
        if check_pubkey_format(outputAddress):
            outputAddresses[i] = validate_checksum(outputAddress)
    if outputBackChange:
        if check_pubkey_format(outputBackChange):
            outputBackChange = validate_checksum(outputBackChange)
    if enough_source:
        message_exit(
            display_pubkey_and_checksum(issuer_pubkey)
            + " pubkey doesn’t have enough money for this transaction."
        )
    return outputBackChange


async def transaction_confirmation(
    issuer_pubkey,
    pubkey_amount,
    tx_amounts,
    outputAddresses,
    outputBackChange,
    comment,
):
    """
    Generate transaction confirmation
    """

    currency_symbol = await CurrencySymbol().symbol
    ud_value = await money.UDValue().ud_value
    total_tx_amount = sum(tx_amounts)
    tx = list()
    # display account situation
    display_amount(
        tx,
        "Initial balance",
        pubkey_amount,
        ud_value,
        currency_symbol,
    )
    display_amount(
        tx,
        "Total transaction amount",
        total_tx_amount,
        ud_value,
        currency_symbol,
    )
    display_amount(
        tx,
        "Balance after transaction",
        (pubkey_amount - total_tx_amount),
        ud_value,
        currency_symbol,
    )
    await display_pubkey(tx, "From", issuer_pubkey)
    # display outputs and amounts
    for outputAddress, tx_amount in zip(outputAddresses, tx_amounts):
        await display_pubkey(tx, "To", outputAddress)
        await sleep(ASYNC_SLEEP)
        display_amount(tx, "Amount", tx_amount, ud_value, currency_symbol)
    # display last informations
    if outputBackChange:
        await display_pubkey(tx, "Backchange", outputBackChange)
    tx.append(["Comment", comment])
    return tx


async def get_list_input_for_transaction(pubkey, TXamount):
    listinput, amount = await money.get_sources(pubkey)

    # generate final list source
    listinputfinal = []
    totalAmountInput = 0
    intermediatetransaction = False
    for input in listinput:
        listinputfinal.append(input)
        totalAmountInput += money.amount_in_current_base(input)
        TXamount -= money.amount_in_current_base(input)
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
    key,
    issuers,
    tx_amounts,
    outputAddresses,
    Comment="",
    OutputbackChange=None,
):
    client = ClientInstance().client
    while True:
        listinput_and_amount = await get_list_input_for_transaction(
            issuers, sum(tx_amounts)
        )
        intermediatetransaction = listinput_and_amount[2]

        if intermediatetransaction:
            totalAmountInput = listinput_and_amount[1]
            await generate_and_send_transaction(
                key,
                issuers,
                [totalAmountInput],
                listinput_and_amount,
                [issuers],
                "Change operation",
            )
            await sleep(1)  # wait 1 second before sending a new transaction

        else:
            await generate_and_send_transaction(
                key,
                issuers,
                tx_amounts,
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
    tx_amounts,
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
    print("   - From:    " + display_pubkey_and_checksum(issuers))
    for tx_amount, outputAddress in zip(tx_amounts, outputAddresses):
        display_sent_tx(outputAddress, tx_amount)
    print("   - Total:   " + str(sum(tx_amounts) / 100))

    client = ClientInstance().client
    transaction = await generate_transaction_document(
        issuers,
        tx_amounts,
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
    print(
        "   - To:     ",
        display_pubkey_and_checksum(outputAddress),
        "\n   - Amount: ",
        amount / 100,
    )


async def generate_transaction_document(
    issuers,
    tx_amounts,
    listinput_and_amount,
    outputAddresses,
    Comment="",
    OutputbackChange=None,
):

    listinput = listinput_and_amount[0]
    totalAmountInput = listinput_and_amount[1]
    total_tx_amount = sum(tx_amounts)

    head_block = await HeadBlock().head_block
    currency_name = head_block["currency"]
    blockstamp_current = BlockUID(head_block["number"], head_block["hash"])
    curentUnitBase = head_block["unitbase"]

    if not OutputbackChange:
        OutputbackChange = issuers

    # if it's not a foreign exchange transaction, we remove units after 2 digits after the decimal point.
    if issuers not in outputAddresses:
        total_tx_amount = (
            total_tx_amount // 10 ** curentUnitBase
        ) * 10 ** curentUnitBase

    # Generate output
    ################
    listoutput = []
    for tx_amount, outputAddress in zip(tx_amounts, outputAddresses):
        generate_output(listoutput, curentUnitBase, tx_amount, outputAddress)

    # Outputs to himself
    rest = totalAmountInput - total_tx_amount
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
        "^[0-9a-zA-Z\\ \\-\\_\\:\\/\\;\\*\\[\\]\\(\\)\\?\\!\\^\\+\\=\\@\\&\\~\\#\\{\\}\\|\\\\<\\>\\%\\.]*$"
    )
    if not search(regex, Comment):
        message_exit("Error: the format of the comment is invalid")


def truncBase(amount, base):
    pow = math.pow(10, base)
    if amount < pow:
        return 0
    return math.trunc(amount / pow) * pow
