from tools import *
import getpass
import os


def auth_method(c):
    if c.contains_switches('auth-scrypt'):
        return auth_by_scrypt(c)
    if c.contains_switches('auth-seed'):
        return auth_by_seed()
    if c.contains_switches('auth-file'):
        return auth_by_auth_file(c)
    print("Error: no authentication method")
    exit()


def generate_auth_file(c):
    if c.contains_definitions('file'):
        file = c.get_definition('file')
    else:
        file = "authfile"
    seed = auth_method(c)
    with open(file, "w") as f:
        f.write(seed)
    print("Authfile generated for the public key: ", get_publickey_from_seed(seed))


def auth_by_auth_file(c):
    if c.contains_definitions('file'):
        file = c.get_definition('file')
    else:
        file = "authfile"
    if not os.path.isfile(file):
        print("Error: the file \"" + file + "\" does not exist")
        exit()
    with open(file) as f:
        seed = f.read()
    regex = re.compile('^[0-9a-fA-F]{64}$')
    if not re.search(regex, seed):
        print("Error: the format of the file is invalid")
        exit()
    return seed


def auth_by_seed():
    seed = input("Please enter your seed on hex format: ")
    regex = re.compile('^[0-9a-fA-F]{64}$')
    if not re.search(regex, seed):
        print("Error: the format of the seed is invalid")
        exit()
    return seed


def auth_by_scrypt(c):
    salt = input("Please enter your Scrypt Salt (Secret identifier): ")
    password = getpass.getpass("Please enter your Scrypt password (masked): ")
    if c.contains_definitions('n') and c.contains_definitions('r') and c.contains_definitions('p'):
        n, r, p = c.get_definition('n'), c.get_definition('r'), c.get_definition('p')
        if n.isnumeric() and r.isnumeric() and p.isnumeric():
            n, r, p = int(n), int(r), int(p)
            if n <= 0 or n > 65536 or r <= 0 or r > 512 or p <= 0 or p > 32:
                print("Error: the values of Scrypt parameters are not good")
                exit(1)
        else:
            print("one of n, r or p is not a number")
            exit(1)
    else:
        print("Using default values. Scrypt parameters not specified or wrong format")
        n, r, p = 4096, 16, 1
    print("Scrypt parameters used: N: {0}, r: {1}, p: {2}".format(n, r, p))

    return get_seed_from_scrypt(salt, password, n, r, p)
