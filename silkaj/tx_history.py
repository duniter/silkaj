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

from click import command, argument, option, echo_via_pager, get_terminal_size
from texttable import Texttable
from operator import itemgetter, neg, eq, ne
from time import time

from duniterpy.api.bma.tx import history
from duniterpy.documents.transaction import Transaction

from silkaj.network_tools import ClientInstance
from silkaj.tools import coroutine
from silkaj.tui import convert_time, display_pubkey_and_checksum
from silkaj.crypto_tools import validate_checksum, check_pubkey_format
from silkaj import wot
from silkaj.money import get_amount_from_pubkey, amount_in_current_base, UDValue
from silkaj.tools import CurrencySymbol


@command("history", help="Display transaction history")
@argument("pubkey")
@option("--uids", "-u", is_flag=True, help="Display uids")
@option("--full-pubkey", "-f", is_flag=True, help="Display full-length pubkeys")
@coroutine
async def transaction_history(pubkey, uids, full_pubkey):
    if check_pubkey_format(pubkey):
        pubkey = validate_checksum(pubkey)

    client = ClientInstance().client
    ud_value = await UDValue().ud_value
    currency_symbol = await CurrencySymbol().symbol

    header = await generate_header(pubkey, currency_symbol, ud_value)
    received_txs, sent_txs = list(), list()
    await get_transactions_history(client, pubkey, received_txs, sent_txs)
    remove_duplicate_txs(received_txs, sent_txs)
    txs_list = await generate_table(
        received_txs, sent_txs, pubkey, ud_value, currency_symbol, uids, full_pubkey
    )
    table = Texttable(max_width=get_terminal_size()[0])
    table.add_rows(txs_list)
    await client.close()
    echo_via_pager(header + table.draw())


async def generate_header(pubkey, currency_symbol, ud_value):
    try:
        idty = await wot.identity_of(pubkey)
    except:
        idty = dict([("uid", "")])
    balance = await get_amount_from_pubkey(pubkey)
    return "Transactions history from: {uid} {pubkey}\n\
Current balance: {balance} {currency}, {balance_ud} UD {currency} on the {date}\n\
".format(
        uid=idty["uid"],
        pubkey=display_pubkey_and_checksum(pubkey),
        currency=currency_symbol,
        balance=balance[1] / 100,
        balance_ud=round(balance[1] / ud_value, 2),
        date=convert_time(time(), "all"),
    )


async def get_transactions_history(client, pubkey, received_txs, sent_txs):
    """
    Get transaction history
    Store txs in Transaction object
    """
    tx_history = await client(history, pubkey)
    currency = tx_history["currency"]

    for received in tx_history["history"]["received"]:
        received_txs.append(Transaction.from_bma_history(currency, received))
    for sent in tx_history["history"]["sent"]:
        sent_txs.append(Transaction.from_bma_history(currency, sent))


def remove_duplicate_txs(received_txs, sent_txs):
    """
    Remove duplicate transactions from history
    Remove received tx which contains output back return
    that we don’t want to displayed
    A copy of received_txs is necessary to remove elements
    """
    for received_tx in list(received_txs):
        if received_tx in sent_txs:
            received_txs.remove(received_tx)


async def generate_table(
    received_txs, sent_txs, pubkey, ud_value, currency_symbol, uids, full_pubkey
):
    """
    Generate information in a list of lists for texttabe
    Merge received and sent txs
    Insert table header at the end not to disturb its generation
    Sort txs temporarily
    """

    received_txs_table, sent_txs_table = list(), list()
    await parse_received_tx(
        received_txs_table, received_txs, pubkey, ud_value, uids, full_pubkey
    )
    await parse_sent_tx(sent_txs_table, sent_txs, pubkey, ud_value, uids, full_pubkey)
    txs_table = received_txs_table + sent_txs_table

    table_titles = [
        "Date",
        "Issuers/Recipients",
        "Amounts {}".format(currency_symbol),
        "Amounts UD{}".format(currency_symbol),
        "Comment",
    ]
    txs_table.insert(0, table_titles)

    txs_table.sort(key=itemgetter(0), reverse=True)
    return txs_table


async def parse_received_tx(
    received_txs_table, received_txs, pubkey, ud_value, uids, full_pubkey
):
    """
    Extract issuers’ pubkeys
    Get identities from pubkeys
    Convert time into human format
    Assign identities
    Get amounts and assign amounts and amounts_ud
    Append comment
    """
    issuers = list()
    for received_tx in received_txs:
        for issuer in received_tx.issuers:
            issuers.append(issuer)
    identities = await wot.identities_from_pubkeys(issuers, uids)
    for received_tx in received_txs:
        tx_list = list()
        tx_list.append(convert_time(received_tx.time, "all"))
        tx_list.append(str())
        for i, issuer in enumerate(received_tx.issuers):
            tx_list[1] += prefix(None, None, i) + assign_idty_from_pubkey(
                issuer, identities, full_pubkey
            )
        amounts = tx_amount(received_tx, pubkey, received_func)[0]
        tx_list.append(amounts / 100)
        tx_list.append(amounts / ud_value)
        tx_list.append(received_tx.comment)
        received_txs_table.append(tx_list)


async def parse_sent_tx(sent_txs_table, sent_txs, pubkey, ud_value, uids, full_pubkey):
    """
    Extract recipients’ pubkeys from outputs
    Get identities from pubkeys
    Convert time into human format
    Store "Total" and total amounts according to the number of outputs
    If not output back return:
    Assign amounts, amounts_ud, identities, and comment
    """
    pubkeys = list()
    for sent_tx in sent_txs:
        outputs = tx_amount(sent_tx, pubkey, sent_func)[1]
        for output in outputs:
            if output_available(output.condition, ne, pubkey):
                pubkeys.append(output.condition.left.pubkey)

    identities = await wot.identities_from_pubkeys(pubkeys, uids)
    for sent_tx in sent_txs:
        tx_list = list()
        tx_list.append(convert_time(sent_tx.time, "all"))

        total_amount, outputs = tx_amount(sent_tx, pubkey, sent_func)
        if len(outputs) > 1:
            tx_list.append("Total")
            amounts = str(total_amount / 100)
            amounts_ud = str(round(total_amount / ud_value, 2))
        else:
            tx_list.append(str())
            amounts = str()
            amounts_ud = str()

        for i, output in enumerate(outputs):
            if output_available(output.condition, ne, pubkey):
                amounts += prefix(None, outputs, i) + str(
                    neg(amount_in_current_base(output)) / 100
                )
                amounts_ud += prefix(None, outputs, i) + str(
                    round(neg(amount_in_current_base(output)) / ud_value, 2)
                )
                tx_list[1] += prefix(tx_list[1], outputs, 0) + assign_idty_from_pubkey(
                    output.condition.left.pubkey, identities, full_pubkey
                )
        tx_list.append(amounts)
        tx_list.append(amounts_ud)
        tx_list.append(sent_tx.comment)
        sent_txs_table.append(tx_list)


def tx_amount(tx, pubkey, function):
    """
    Determine transaction amount from output sources
    """
    amount = 0
    outputs = list()
    for output in tx.outputs:
        if output_available(output.condition, ne, pubkey):
            outputs.append(output)
        amount += function(output, pubkey)
    return amount, outputs


def received_func(output, pubkey):
    if output_available(output.condition, eq, pubkey):
        return amount_in_current_base(output)
    return 0


def sent_func(output, pubkey):
    if output_available(output.condition, ne, pubkey):
        return neg(amount_in_current_base(output))
    return 0


def output_available(condition, comparison, value):
    """
    Check if output source is available
    Currently only handle simple SIG condition
    XHX, CLTV, CSV should be handled when present in the blockchain
    """
    if hasattr(condition.left, "pubkey"):
        return comparison(condition.left.pubkey, value)
    else:
        return False


def assign_idty_from_pubkey(pubkey, identities, full_pubkey):
    idty = display_pubkey_and_checksum(pubkey, short=not full_pubkey)
    for identity in identities:
        if pubkey == identity["pubkey"]:
            idty = "{0} - {1}".format(
                identity["uid"],
                display_pubkey_and_checksum(pubkey, short=not full_pubkey),
            )
    return idty


def prefix(tx_addresses, outputs, occurence):
    """
    Pretty print with texttable
    Break line when several values in a cell

    Received tx case, 'outputs' is not defined, then add a breakline
    between the pubkeys except for the first occurence for multi-sig support

    Sent tx case, handle "Total" line in case of multi-output txs
    In case of multiple outputs, there is a "Total" on the top,
    where there must be a breakline
    """

    if not outputs:
        return "\n" if occurence > 0 else ""

    if tx_addresses == "Total":
        return "\n"
    return "\n" if len(outputs) > 1 else ""
