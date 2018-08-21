from silkaj.network_tools import get_request, HeadBlock
from silkaj.tools import get_publickey_from_seed, CurrencySymbol
from silkaj.auth import auth_method
from silkaj.wot import check_public_key


def cmd_amount(ep, cli_args):
    if not cli_args.subsubcmd.startswith("--"):
        pubkeys = cli_args.subsubcmd.split(":")
        for pubkey in pubkeys:
            pubkey = check_public_key(pubkey, True)
            if not pubkey:
                return
        total = [0, 0]
        for pubkey in pubkeys:
            value = get_amount_from_pubkey(ep, pubkey)
            show_amount_from_pubkey(ep, pubkey, value)
            total[0] += value[0]
            total[1] += value[1]
        if (len(pubkeys) > 1):
            show_amount_from_pubkey(ep, "Total", total)
    else:
        seed = auth_method(cli_args)
        pubkey = get_publickey_from_seed(seed)
        show_amount_from_pubkey(ep, pubkey, get_amount_from_pubkey(ep, pubkey))


def show_amount_from_pubkey(ep, pubkey, value):
    totalAmountInput = value[0]
    amount = value[1]
    # output

    currency_symbol = CurrencySymbol(ep).symbol
    ud_value = UDValue(ep).ud_value
    if totalAmountInput - amount != 0:
        print("Blockchain:")
        print("-----------")
        print("Relative     =", round(amount / ud_value, 2), "UD", currency_symbol)
        print("Quantitative =",  round(amount / 100, 2), currency_symbol + "\n")

        print("Pending Transaction:")
        print("--------------------")
        print("Relative     =",  round((totalAmountInput - amount) / ud_value, 2), "UD", currency_symbol)
        print("Quantitative =",  round((totalAmountInput - amount) / 100, 2), currency_symbol + "\n")

    print("Total amount of: " + pubkey)
    print("----------------------------------------------------------------")
    print("Total Relative     =",  round(totalAmountInput / ud_value, 2), "UD", currency_symbol)
    print("Total Quantitative =",  round(totalAmountInput / 100, 2), currency_symbol + "\n")


def get_amount_from_pubkey(ep, pubkey):
    sources = get_request(ep, "tx/sources/" + pubkey)["sources"]

    listinput = []
    amount = 0
    for source in sources:
        if source["conditions"] == "SIG(" + pubkey + ")":
            amount += source["amount"] * 10 ** source["base"]
            listinput.append(str(source["amount"]) + ":" +
                             str(source["base"]) + ":" +
                             str(source["type"]) + ":" +
                             str(source["identifier"]) + ":" +
                             str(source["noffset"]))

    # pending source
    history = get_request(ep, "tx/history/" + pubkey + "/pending")["history"]
    pendings = history["sending"] + history["receiving"] + history["pending"]
    # print(pendings)

    last_block_number = int(HeadBlock(ep).head_block["number"])

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
                                        str(outputsplited[0]) + ":" +
                                        str(outputsplited[1]) + ":T:" +
                                        identifier + ":" + str(i)
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

    totalAmountInput = 0
    for input in listinput:
        inputsplit = input.split(":")
        totalAmountInput += int(inputsplit[0]) * 10 ** int(inputsplit[1])

    return int(totalAmountInput), int(amount)


class UDValue(object):
    __instance = None

    def __new__(cls, ep):
        if UDValue.__instance is None:
            UDValue.__instance = object.__new__(cls)
        return UDValue.__instance

    def __init__(self, ep):
        blockswithud = get_request(ep, "blockchain/with/ud")["result"]
        NBlastUDblock = blockswithud["blocks"][-1]
        lastUDblock = get_request(ep, "blockchain/block/" + str(NBlastUDblock))
        self.ud_value = lastUDblock["dividend"] * 10 ** lastUDblock["unitbase"]
