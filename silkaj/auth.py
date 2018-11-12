from silkaj.crypto_tools import get_publickey_from_seed, b58_decode, xor_bytes
from silkaj.tools import message_exit
from nacl import encoding
import nacl.hash
from scrypt import hash
import pyaes
from getpass import getpass
from os import path
from re import compile, search


def auth_method(cli_args):
    if cli_args.contains_switches("auth-seed"):
        return auth_by_seed()
    if cli_args.contains_switches("auth-file"):
        return auth_by_auth_file(cli_args)
    if cli_args.contains_switches("auth-wif"):
        return auth_by_wif()
    else:
        return auth_by_scrypt(cli_args)


def generate_auth_file(cli_args):
    if cli_args.contains_definitions("file"):
        file = cli_args.get_definition("file")
    else:
        file = "authfile"
    seed = auth_method(cli_args)
    with open(file, "w") as f:
        f.write(seed)
    print(
        "Authentication file 'authfile' generated and stored in current\
 folder for following public key:",
        get_publickey_from_seed(seed),
    )


def auth_by_auth_file(cli_args):
    if cli_args.contains_definitions("file"):
        file = cli_args.get_definition("file")
    else:
        file = "authfile"
    if not path.isfile(file):
        message_exit('Error: the file "' + file + '" does not exist')
    with open(file) as f:
        filetxt = f.read()

    regex_seed = compile("^[0-9a-fA-F]{64}$")
    regex_gannonce = compile(
        "^pub: [1-9A-HJ-NP-Za-km-z]{43,44}\nsec: [1-9A-HJ-NP-Za-km-z]{88,90}.*$"
    )
    # Seed Format
    if search(regex_seed, filetxt):
        seed = filetxt[0:64]
    # gannonce.duniter.org Format
    elif search(regex_gannonce, filetxt):
        private_key = filetxt.split("sec: ")[1].split("\n")[0]
        seed = encoding.HexEncoder.encode(b58_decode(private_key))[0:64].decode("utf-8")
    else:
        message_exit("Error: the format of the file is invalid")
    return seed


def auth_by_seed():
    seed = input("Please enter your seed on hex format: ")
    regex = compile("^[0-9a-fA-F]{64}$")
    if not search(regex, seed):
        message_exit("Error: the format of the seed is invalid")
    return seed


def auth_by_scrypt(cli_args):
    salt = getpass("Please enter your Scrypt Salt (Secret identifier): ")
    password = getpass("Please enter your Scrypt password (masked): ")

    if (
        cli_args.contains_definitions("n")
        and cli_args.contains_definitions("r")
        and cli_args.contains_definitions("p")
    ):
        n, r, p = (
            cli_args.get_definition("n"),
            cli_args.get_definition("r"),
            cli_args.get_definition("p"),
        )
        if n.isnumeric() and r.isnumeric() and p.isnumeric():
            n, r, p = int(n), int(r), int(p)
            if n <= 0 or n > 65536 or r <= 0 or r > 512 or p <= 0 or p > 32:
                message_exit("Error: the values of Scrypt parameters are not good")
        else:
            message_exit("one of n, r or p is not a number")
    else:
        print("Using default values. Scrypt parameters not specified or wrong format")
        n, r, p = 4096, 16, 1
    print("Scrypt parameters used: N: {0}, r: {1}, p: {2}".format(n, r, p))

    return get_seed_from_scrypt(salt, password, n, r, p)


def auth_by_wif():
    wif = input("Please enter your WIF or Encrypted WIF address: ")

    regex = compile("^[1-9A-HJ-NP-Za-km-z]*$")
    if not search(regex, wif):
        message_exit("Error: the format of WIF is invalid")

    wif_bytes = b58_decode(wif)
    fi = wif_bytes[0:1]

    if fi == b"\x01":
        return get_seed_from_wifv1(wif)
    elif fi == b"\x02":
        password = getpass("Please enter the " + "password of WIF (masked): ")
        return get_seed_from_ewifv1(wif, password)

    message_exit("Error: the format of WIF is invalid or unknown")


def get_seed_from_scrypt(salt, password, N=4096, r=16, p=1):
    seed = hash(password, salt, N, r, p, 32)
    seedhex = encoding.HexEncoder.encode(seed).decode("utf-8")
    return seedhex


def get_seed_from_wifv1(wif):
    regex = compile("^[1-9A-HJ-NP-Za-km-z]*$")
    if not search(regex, wif):
        message_exit("Error: the format of WIF is invalid")

    wif_bytes = b58_decode(wif)
    if len(wif_bytes) != 35:
        message_exit("Error: the size of WIF is invalid")

    checksum_from_wif = wif_bytes[-2:]
    fi = wif_bytes[0:1]
    seed = wif_bytes[1:-2]
    seed_fi = wif_bytes[0:-2]

    if fi != b"\x01":
        message_exit("Error: It's not a WIF format")

    # checksum control
    checksum = nacl.hash.sha256(
        nacl.hash.sha256(seed_fi, encoding.RawEncoder), encoding.RawEncoder
    )[0:2]
    if checksum_from_wif != checksum:
        message_exit("Error: bad checksum of the WIF")

    seedhex = encoding.HexEncoder.encode(seed).decode("utf-8")
    return seedhex


def get_seed_from_ewifv1(ewif, password):
    regex = compile("^[1-9A-HJ-NP-Za-km-z]*$")
    if not search(regex, ewif):
        message_exit("Error: the format of EWIF is invalid")

    wif_bytes = b58_decode(ewif)
    if len(wif_bytes) != 39:
        message_exit("Error: the size of EWIF is invalid")

    wif_no_checksum = wif_bytes[0:-2]
    checksum_from_ewif = wif_bytes[-2:]
    fi = wif_bytes[0:1]
    salt = wif_bytes[1:5]
    encryptedhalf1 = wif_bytes[5:21]
    encryptedhalf2 = wif_bytes[21:37]

    if fi != b"\x02":
        message_exit("Error: It's not a EWIF format")

    # Checksum Control
    checksum = nacl.hash.sha256(
        nacl.hash.sha256(wif_no_checksum, encoding.RawEncoder), encoding.RawEncoder
    )[0:2]
    if checksum_from_ewif != checksum:
        message_exit("Error: bad checksum of EWIF address")

    # SCRYPT
    password = password.encode("utf-8")
    scrypt_seed = hash(password, salt, 16384, 8, 8, 64)
    derivedhalf1 = scrypt_seed[0:32]
    derivedhalf2 = scrypt_seed[32:64]

    # AES
    aes = pyaes.AESModeOfOperationECB(derivedhalf2)
    decryptedhalf1 = aes.decrypt(encryptedhalf1)
    decryptedhalf2 = aes.decrypt(encryptedhalf2)

    # XOR
    seed1 = xor_bytes(decryptedhalf1, derivedhalf1[0:16])
    seed2 = xor_bytes(decryptedhalf2, derivedhalf1[16:32])
    seed = seed1 + seed2
    seedhex = encoding.HexEncoder.encode(seed).decode("utf-8")

    # Password Control
    salt_from_seed = nacl.hash.sha256(
        nacl.hash.sha256(
            b58_decode(get_publickey_from_seed(seedhex)), encoding.RawEncoder
        ),
        encoding.RawEncoder,
    )[0:4]
    if salt_from_seed != salt:
        message_exit("Error: bad Password of EWIF address")

    return seedhex
