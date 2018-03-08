import datetime
import nacl.encoding
import nacl.signing
import nacl.hash
import re
import sys

from network_tools import *
from constants import *


def convert_time(timestamp, kind):
    ts = int(timestamp)
    if kind == "all":
        pattern = "%Y-%m-%d %H:%M:%S"
    elif kind == "hour":
        if ts >= 3600:
            pattern = "%H:%M:%S"
        else:
            pattern = "%M:%S"
    return datetime.datetime.fromtimestamp(ts).strftime(pattern)


def get_currency_symbol(currency):
    if currency == "g1":
        return G1_SYMBOL
    elif currency == "g1-test":
        return GTEST_SYMBOL


def sign_document_from_seed(document, seed):
    seed = bytes(seed, 'utf-8')
    signing_key = nacl.signing.SigningKey(seed, nacl.encoding.HexEncoder)
    signed = signing_key.sign(bytes(document, 'utf-8'))
    signed_b64 = nacl.encoding.Base64Encoder.encode(signed.signature)
    return signed_b64.decode("utf-8")


def get_publickey_from_seed(seed):
    seed = bytes(seed, 'utf-8')
    seed = nacl.encoding.HexEncoder.decode(seed)
    public_key, secret_key = nacl.bindings.crypto_sign_seed_keypair(seed)
    return b58_encode(public_key)


def check_public_key(pubkey, display_error):
    """
    Check public key format
    Check pubkey checksum which could be append after the pubkey
    If check pass: return pubkey
    """
    regex = re.compile('^[1-9A-HJ-NP-Za-km-z]{43,44}$')
    regex_checksum = re.compile('^[1-9A-HJ-NP-Za-km-z]{43,44}' +
                                ':[1-9A-HJ-NP-Za-km-z]{3}$')
    if re.search(regex, pubkey):
        return pubkey
    elif re.search(regex_checksum, pubkey):
        pubkey, checksum = pubkey.split(":")
        pubkey_byte = b58_decode(pubkey)
        checksum_calculed = b58_encode(nacl.hash.sha256(
                    nacl.hash.sha256(pubkey_byte, nacl.encoding.RawEncoder),
                    nacl.encoding.RawEncoder))[:3]
        if checksum_calculed == checksum:
            return pubkey
        else:
            print("error: bad checksum of the public key")
            return False

    elif display_error:
        print("Error: the format of the public key is invalid")
    return False


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


def get_last_ud_value(ep):
    blockswithud = get_request(ep, "blockchain/with/ud")["result"]
    NBlastUDblock = blockswithud["blocks"][-1]
    lastUDblock = get_request(ep, "blockchain/block/" + str(NBlastUDblock))
    return lastUDblock["dividend"] * 10 ** lastUDblock["unitbase"]


b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58_encode(b):

    # Convert big-endian bytes to integer
    n = int('0x0' + nacl.encoding.HexEncoder.encode(b).decode('utf8'), 16)

    # Divide that integer into base58
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(b58_digits[r])
    res = ''.join(res[::-1])

    # Encode leading zeros as base58 zeros
    czero = 0
    pad = 0
    for c in b:
        if c == czero:
            pad += 1
        else:
            break
    return b58_digits[0] * pad + res


def b58_decode(s):
    if not s:
        return b''

    # Convert the string to an integer
    n = 0
    for c in s:
        n *= 58
        if c not in b58_digits:
            raise InvalidBase58Error('Character %r is not a ' +
                                     'valid base58 character' % c)
        digit = b58_digits.index(c)
        n += digit

    # Convert the integer to bytes
    h = '%x' % n
    if len(h) % 2:
        h = '0' + h
    res = nacl.encoding.HexEncoder.decode(h.encode('utf8'))

    # Add padding back.
    pad = 0
    for c in s[:-1]:
        if c == b58_digits[0]:
            pad += 1
        else:
            break
    return b'\x00' * pad + res


def xor_bytes(b1, b2):
    result = bytearray()
    for b1, b2 in zip(b1, b2):
        result.append(b1 ^ b2)
    return result

def message_exit(message):
    print(message)
    sys.exit(1)
