from tools import *
import getpass
import os

def auth_method(c):
    if c.contains_switches('auth-scrypt'):
        return auth_by_scrypt()
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


def auth_by_scrypt():
    salt = input("Please enter your Scrypt Salt (Secret identifier): ")
    password = getpass.getpass("Please enter your Scrypt password (masked): ")
    scrypt_param = input("Please enter your Scrypt parameters (N,r,p): default [4096,16,1]: ")
    if not scrypt_param:
        scrypt_param = "4096,16,1"
    scrypt_param_splited= scrypt_param.split(",")
    n = int(scrypt_param_splited[0])
    r = int(scrypt_param_splited[1])
    p = int(scrypt_param_splited[2])
    if (n <= 0 or n > 65536 or r <= 0 or r > 512 or p <= 0 or p > 32):
        print("Error: the values of Scrypt parameters are not good")

    return get_seed_from_scrypt(salt, password, n, r, p)
