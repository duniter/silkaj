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

from silkaj.network_tools import ClientInstance, HeadBlock
from silkaj.crypto_tools import get_publickey_from_seed
from silkaj.tools import CurrencySymbol
from silkaj.auth import auth_method
from silkaj.wot import check_public_key
from duniterpy.api.bma import tx, blockchain


async def cmd_amount(cli_args):
    client = ClientInstance().client
    if not cli_args.subsubcmd.startswith("--auth-"):
        pubkeys = cli_args.subsubcmd.split(":")
        for pubkey in pubkeys:
            pubkey = check_public_key(pubkey, True)
            if not pubkey:
                return
        total = [0, 0]
        for pubkey in pubkeys:
            value = await get_amount_from_pubkey(pubkey)
            show_amount_from_pubkey(pubkey, value)
            total[0] += value[0]
            total[1] += value[1]
        if len(pubkeys) > 1:
            show_amount_from_pubkey("Total", total)
    else:
        seed = auth_method(cli_args)
        pubkey = get_publickey_from_seed(seed)
        await show_amount_from_pubkey(pubkey, await get_amount_from_pubkey(pubkey))
    await client.close()


def show_amount_from_pubkey(pubkey, value):
    totalAmountInput = value[0]
    amount = value[1]
    # output

    currency_symbol = CurrencySymbol().symbol
    ud_value = UDValue().ud_value
    average, monetary_mass = get_average()
    if totalAmountInput - amount != 0:
        print("Blockchain:")
        print("-----------")
        print("Relative     =", round(amount / ud_value, 2), "UD", currency_symbol)
        print("Quantitative =", round(amount / 100, 2), currency_symbol + "\n")

        print("Pending Transaction:")
        print("--------------------")
        print(
            "Relative     =",
            round((totalAmountInput - amount) / ud_value, 2),
            "UD",
            currency_symbol,
        )
        print(
            "Quantitative =",
            round((totalAmountInput - amount) / 100, 2),
            currency_symbol + "\n",
        )

    print("Total amount of: " + pubkey)
    print("----------------------------------------------------------------")
    print(
        "Total Relative     =",
        round(totalAmountInput / ud_value, 2),
        "UD",
        currency_symbol,
    )
    print("Total Quantitative =", round(totalAmountInput / 100, 2), currency_symbol)
    print(
        "Total Relative to average money share =",
        round(totalAmountInput / average, 2),
        "× M/N",
    )
    print(
        "Total Relative to monetary mass       =",
        round((totalAmountInput / monetary_mass) * 100, 3),
        "% M" + "\n",
    )


def get_average():
    head = HeadBlock().head_block
    monetary_mass = head["monetaryMass"]
    members_count = head["membersCount"]
    average = monetary_mass / members_count
    return average, monetary_mass


async def get_amount_from_pubkey(pubkey):
    listinput, amount = await get_sources(pubkey)

    totalAmountInput = 0
    for input in listinput:
        inputsplit = input.split(":")
        totalAmountInput += int(inputsplit[0]) * 10 ** int(inputsplit[1])

    return totalAmountInput, amount


async def get_sources(pubkey):
    client = ClientInstance().client
    # Sources written into the blockchain
    sources = await client(tx.sources, pubkey)

    listinput = []
    amount = 0
    for source in sources["sources"]:
        if source["conditions"] == "SIG(" + pubkey + ")":
            amount += source["amount"] * 10 ** source["base"]
            listinput.append(
                str(source["amount"])
                + ":"
                + str(source["base"])
                + ":"
                + source["type"]
                + ":"
                + source["identifier"]
                + ":"
                + str(source["noffset"])
            )

    # pending source
    history = await client(tx.pending, pubkey)
    history = history["history"]
    pendings = history["sending"] + history["receiving"] + history["pending"]

    last_block_number = HeadBlock().head_block["number"]

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
                if outputsplited[2] == "SIG(" + pubkey + ")":
                    inputgenerated = (
                        outputsplited[0]
                        + ":"
                        + outputsplited[1]
                        + ":T:"
                        + identifier
                        + ":"
                        + str(i)
                    )
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

    return listinput, amount


class UDValue(object):
    __instance = None

    def __new__(cls):
        if UDValue.__instance is None:
            UDValue.__instance = object.__new__(cls)
        return UDValue.__instance

    def __init__(self):
        blockswithud = get_request("blockchain/with/ud")["result"]
        NBlastUDblock = blockswithud["blocks"][-1]
        lastUDblock = get_request("blockchain/block/" + str(NBlastUDblock))
        self.ud_value = lastUDblock["dividend"] * 10 ** lastUDblock["unitbase"]
