from nacl import encoding, signing, hash, bindings
from re import compile, search


def sign_document_from_seed(document, seed):
    seed = bytes(seed, "utf-8")
    signing_key = signing.SigningKey(seed, encoding.HexEncoder)
    signed = signing_key.sign(bytes(document, "utf-8"))
    signed_b64 = encoding.Base64Encoder.encode(signed.signature)
    return signed_b64.decode("utf-8")


def get_publickey_from_seed(seed):
    seed = bytes(seed, "utf-8")
    seed = encoding.HexEncoder.decode(seed)
    public_key, secret_key = bindings.crypto_sign_seed_keypair(seed)
    return b58_encode(public_key)


def check_public_key(pubkey, display_error):
    """
    Check public key format
    Check pubkey checksum which could be append after the pubkey
    If check pass: return pubkey
    """
    regex = compile("^[1-9A-HJ-NP-Za-km-z]{43,44}$")
    regex_checksum = compile(
        "^[1-9A-HJ-NP-Za-km-z]{43,44}" + "![1-9A-HJ-NP-Za-km-z]{3}$"
    )
    if search(regex, pubkey):
        return pubkey
    elif search(regex_checksum, pubkey):
        pubkey, checksum = pubkey.split("!")
        pubkey_byte = b58_decode(pubkey)
        checksum_calculed = b58_encode(
            hash.sha256(
                hash.sha256(pubkey_byte, encoding.RawEncoder), encoding.RawEncoder
            )
        )[:3]
        if checksum_calculed == checksum:
            return pubkey
        else:
            print("Error: bad checksum for following public key:")
            return False

    elif display_error:
        print("Error: bad format for following public key:")
    return False


b58_digits = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58_encode(b):

    # Convert big-endian bytes to integer
    n = int("0x0" + encoding.HexEncoder.encode(b).decode("utf8"), 16)

    # Divide that integer into base58
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(b58_digits[r])
    res = "".join(res[::-1])

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
        return b""

    # Convert the string to an integer
    n = 0
    for c in s:
        n *= 58
        if c not in b58_digits:
            raise InvalidBase58Error(
                "Character %r is not a " + "valid base58 character" % c
            )
        digit = b58_digits.index(c)
        n += digit

    # Convert the integer to bytes
    h = "%x" % n
    if len(h) % 2:
        h = "0" + h
    res = encoding.HexEncoder.decode(h.encode("utf8"))

    # Add padding back.
    pad = 0
    for c in s[:-1]:
        if c == b58_digits[0]:
            pad += 1
        else:
            break
    return b"\x00" * pad + res


def xor_bytes(b1, b2):
    result = bytearray()
    for b1, b2 in zip(b1, b2):
        result.append(b1 ^ b2)
    return result
