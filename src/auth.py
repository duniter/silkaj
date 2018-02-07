from tools import *
import nacl.encoding
import nacl.signing
import nacl.hash
import scrypt
import pyaes
import getpass
import os
import sys


def auth_method(c):
    if c.contains_switches('auth-scrypt'):
        return auth_by_scrypt(c)
    if c.contains_switches('auth-seed'):
        return auth_by_seed()
    if c.contains_switches('auth-file'):
        return auth_by_auth_file(c)
    if c.contains_switches('auth-wif'):
        return auth_by_wif()
    print("Error: no authentication method")
    sys.exit(1)


def generate_auth_file(c):
    if c.contains_definitions('file'):
        file = c.get_definition('file')
    else:
        file = "authfile"
    seed = auth_method(c)
    with open(file, "w") as f:
        f.write(seed)
    print("Authfile generated for the public key: ",
          get_publickey_from_seed(seed))


def auth_by_auth_file(c):
    if c.contains_definitions('file'):
        file = c.get_definition('file')
    else:
        file = "authfile"
    if not os.path.isfile(file):
        print("Error: the file \"" + file + "\" does not exist")
        sys.exit(1)
    with open(file) as f:
        filetxt = f.read()

    regex_seed = re.compile('^[0-9a-fA-F]{64}$')
    regex_gannonce = re.compile('^pub: [1-9A-HJ-NP-Za-km-z]{43,44}\nsec: [1-9A-HJ-NP-Za-km-z]{88,90}.*$')
    # Seed Format
    if re.search(regex_seed, filetxt):
        seed = filetxt[0:64]
    # gannonce.duniter.org Format
    elif re.search(regex_gannonce, filetxt):
        private_key = filetxt.split("sec: ")[1].split("\n")[0]
        seed = nacl.encoding.HexEncoder.encode(b58_decode(private_key))[0:64].decode("utf-8")
    else:
        print("Error: the format of the file is invalid")
        sys.exit(1)
    return seed


def auth_by_seed():
    seed = input("Please enter your seed on hex format: ")
    regex = re.compile('^[0-9a-fA-F]{64}$')
    if not re.search(regex, seed):
        print("Error: the format of the seed is invalid")
        sys.exit(1)
    return seed


def auth_by_scrypt(c):
     if c.contains_definitions('salt') and c.contains_definitions('password'):
        salt = c.get_definition('salt')
        password = c.get_definition('password')
    else:
    salt = getpass.getpass("Please enter your Scrypt Salt (Secret identifier): ")
    password = getpass.getpass("Please enter your Scrypt password (masked): ")

    if c.contains_definitions('n') and c.contains_definitions('r') and c.contains_definitions('p'):
        n, r, p = c.get_definition('n'), c.get_definition('r'), c.get_definition('p')
        if n.isnumeric() and r.isnumeric() and p.isnumeric():
            n, r, p = int(n), int(r), int(p)
            if n <= 0 or n > 65536 or r <= 0 or r > 512 or p <= 0 or p > 32:
                print("Error: the values of Scrypt parameters are not good")
                sys.exit(1)
        else:
            print("one of n, r or p is not a number")
            sys.exit(1)
    else:
        print("Using default values. Scrypt parameters not specified or wrong format")
        n, r, p = 4096, 16, 1
    print("Scrypt parameters used: N: {0}, r: {1}, p: {2}".format(n, r, p))

    return get_seed_from_scrypt(salt, password, n, r, p)


def auth_by_wif():
    wif = input("Please enter your WIF or Encrypted WIF address: ")

    regex = re.compile('^[1-9A-HJ-NP-Za-km-z]*$')
    if not re.search(regex, wif):
        print("Error: the format of WIF is invalid")
        sys.exit(1)

    wif_bytes = b58_decode(wif)
    fi = wif_bytes[0:1]

    if fi == b'\x01':
        return get_seed_from_wifv1(wif)
    elif fi == b'\x02':
        password = getpass.getpass("Please enter the " +
                                   "password of WIF (masked): ")
        return get_seed_from_ewifv1(wif, password)

    print("Error: the format of WIF is invalid or unknown")
    sys.exit(1)


def get_seed_from_scrypt(salt, password, N=4096, r=16, p=1):
    seed = scrypt.hash(password, salt, N, r, p, 32)
    seedhex = nacl.encoding.HexEncoder.encode(seed).decode("utf-8")
    return seedhex


def get_seed_from_wifv1(wif):
    regex = re.compile('^[1-9A-HJ-NP-Za-km-z]*$')
    if not re.search(regex, wif):
        print("Error: the format of WIF is invalid")
        sys.exit(1)

    wif_bytes = b58_decode(wif)
    if len(wif_bytes) != 35:
        print("Error: the size of WIF is invalid")
        sys.exit(1)

    checksum_from_wif = wif_bytes[-2:]
    fi = wif_bytes[0:1]
    seed = wif_bytes[1:-2]
    seed_fi = wif_bytes[0:-2]

    if fi != b'\x01':
        print("Error: It's not a WIF format")
        sys.exit(1)

    # checksum control
    checksum = nacl.hash.sha256(
                    nacl.hash.sha256(seed_fi, nacl.encoding.RawEncoder),
                    nacl.encoding.RawEncoder)[0:2]
    if checksum_from_wif != checksum:
        print("Error: bad checksum of the WIF")
        sys.exit(1)

    seedhex = nacl.encoding.HexEncoder.encode(seed).decode("utf-8")
    return seedhex


def get_seed_from_ewifv1(ewif, password):
    regex = re.compile('^[1-9A-HJ-NP-Za-km-z]*$')
    if not re.search(regex, ewif):
        print("Error: the format of EWIF is invalid")
        sys.exit(1)

    wif_bytes = b58_decode(ewif)
    if len(wif_bytes) != 39:
        print("Error: the size of EWIF is invalid")
        sys.exit(1)

    wif_no_checksum = wif_bytes[0:-2]
    checksum_from_ewif = wif_bytes[-2:]
    fi = wif_bytes[0:1]
    salt = wif_bytes[1:5]
    encryptedhalf1 = wif_bytes[5:21]
    encryptedhalf2 = wif_bytes[21:37]

    if fi != b'\x02':
        print("Error: It's not a EWIF format")
        sys.exit(1)

    # Checksum Control
    checksum = nacl.hash.sha256(
                   nacl.hash.sha256(wif_no_checksum, nacl.encoding.RawEncoder),
                   nacl.encoding.RawEncoder)[0:2]
    if checksum_from_ewif != checksum:
        print("Error: bad checksum of EWIF address")
        sys.exit(1)

    # SCRYPT
    password = password.encode("utf-8")
    scrypt_seed = scrypt.hash(password, salt, 16384, 8, 8, 64)
    derivedhalf1 = scrypt_seed[0:32]
    derivedhalf2 = scrypt_seed[32:64]

    # AES
    aes = pyaes.AESModeOfOperationECB(derivedhalf2)
    decryptedhalf1 = aes.decrypt(encryptedhalf1)
    decryptedhalf2 = aes.decrypt(encryptedhalf2)

    # XOR
    seed1 = xor_bytes(decryptedhalf1, derivedhalf1[0:16])
    seed2 = xor_bytes(decryptedhalf2, derivedhalf1[16:32])
    seed = seed1+seed2
    seedhex = nacl.encoding.HexEncoder.encode(seed).decode("utf-8")

    # Password Control
    salt_from_seed = nacl.hash.sha256(
                        nacl.hash.sha256(
                            b58_decode(get_publickey_from_seed(seedhex)),
                            nacl.encoding.RawEncoder),
                        nacl.encoding.RawEncoder)[0:4]
    if salt_from_seed != salt:
        print("Error: bad Password of EWIF address")
        sys.exit(1)

    return seedhex
