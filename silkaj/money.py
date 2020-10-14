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

from click import command, argument, pass_context, echo
from tabulate import tabulate

from silkaj.network_tools import ClientInstance
from silkaj.blockchain_tools import HeadBlock
from silkaj.tools import CurrencySymbol, message_exit, coroutine
from silkaj.auth import auth_method, has_auth_method

# had to import wot to prevent loop dependency. No use here.
from silkaj import wot
from silkaj.crypto_tools import check_pubkey_format, validate_checksum
from silkaj.tui import display_amount, display_pubkey_and_checksum

from duniterpy.api.bma import tx, blockchain
from duniterpy.documents.transaction import InputSource


@command("balance", help="Get wallet balance")
@argument("pubkeys", nargs=-1)
@pass_context
@coroutine
async def cmd_amount(ctx, pubkeys):
    client = ClientInstance().client
    if not has_auth_method():
        if not pubkeys:
            message_exit("You should specify one or many pubkeys")
        pubkey_list = list()
        for pubkey in pubkeys:
            if check_pubkey_format(pubkey):
                pubkey_list.append(validate_checksum(pubkey))
            else:
                pubkey_list.append(pubkey)
        total = [0, 0]
        for pubkey in pubkey_list:
            inputs_balance = await get_amount_from_pubkey(pubkey)
            await show_amount_from_pubkey(pubkey, inputs_balance)
            total[0] += inputs_balance[0]
            total[1] += inputs_balance[1]
        if len(pubkey_list) > 1:
            await show_amount_from_pubkey("Total", total)
    else:
        key = auth_method()
        pubkey = key.pubkey
        await show_amount_from_pubkey(pubkey, await get_amount_from_pubkey(pubkey))
    await client.close()


async def show_amount_from_pubkey(pubkey, inputs_balance):
    totalAmountInput = inputs_balance[0]
    balance = inputs_balance[1]
    currency_symbol = await CurrencySymbol().symbol
    ud_value = await UDValue().ud_value
    average, monetary_mass = await get_average()
    # if `pubkey` is a pubkey, get pubkey:checksum
    if pubkey != "Total":
        pubkey = display_pubkey_and_checksum(pubkey)
    # display balance table
    display = list()
    display.append(["Balance of pubkey", pubkey])
    if totalAmountInput - balance != 0:
        display_amount(display, "Blockchain", balance, ud_value, currency_symbol)
        display_amount(
            display,
            "Pending transaction",
            (totalAmountInput - balance),
            ud_value,
            currency_symbol,
        )
    display_amount(display, "Total amount", totalAmountInput, ud_value, currency_symbol)
    display.append(
        [
            "Total relative to M/N",
            "{0} x M/N".format(round(totalAmountInput / average, 2)),
        ]
    )
    echo(tabulate(display, tablefmt="fancy_grid"))


async def get_average():
    head = await HeadBlock().head_block
    monetary_mass = head["monetaryMass"]
    members_count = head["membersCount"]
    average = monetary_mass / members_count
    return average, monetary_mass


async def get_amount_from_pubkey(pubkey):
    listinput, amount = await get_sources(pubkey)

    totalAmountInput = 0
    for input in listinput:
        totalAmountInput += amount_in_current_base(input)
    return totalAmountInput, amount


async def get_sources(pubkey):
    client = ClientInstance().client
    # Sources written into the blockchain
    sources = await client(tx.sources, pubkey)

    listinput = list()
    amount = 0
    for source in sources["sources"]:
        if source["conditions"] == "SIG(" + pubkey + ")":
            listinput.append(
                InputSource(
                    amount=source["amount"],
                    base=source["base"],
                    source=source["type"],
                    origin_id=source["identifier"],
                    index=source["noffset"],
                )
            )
            amount += amount_in_current_base(listinput[-1])

    # pending source
    history = await client(tx.pending, pubkey)
    history = history["history"]
    pendings = history["sending"] + history["receiving"] + history["pending"]

    # add pending output
    pending_sources = list()
    for pending in pendings:
        identifier = pending["hash"]
        for i, output in enumerate(pending["outputs"]):
            outputsplited = output.split(":")
            if outputsplited[2] == "SIG(" + pubkey + ")":
                inputgenerated = InputSource(
                    amount=int(outputsplited[0]),
                    base=int(outputsplited[1]),
                    source="T",
                    origin_id=identifier,
                    index=i,
                )
                if inputgenerated not in listinput:
                    listinput.append(inputgenerated)

        for input in pending["inputs"]:
            pending_sources.append(InputSource.from_inline(input))

    # remove input already used
    for input in pending_sources:
        if input in listinput:
            listinput.remove(input)

    return listinput, amount


class UDValue(object):
    __instance = None

    def __new__(cls):
        if UDValue.__instance is None:
            UDValue.__instance = object.__new__(cls)
        return UDValue.__instance

    def __init__(self):
        self.ud_value = self.get_ud_value()

    async def get_ud_value(self):
        client = ClientInstance().client
        blockswithud = await client(blockchain.ud)
        NBlastUDblock = blockswithud["result"]["blocks"][-1]
        lastUDblock = await client(blockchain.block, NBlastUDblock)
        return lastUDblock["dividend"] * 10 ** lastUDblock["unitbase"]


def amount_in_current_base(source):
    """
    Get amount in current base from input or output source
    """
    return source.amount * 10 ** source.base
