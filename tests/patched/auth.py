# This file contains patches for auth functions.


def patched_auth_by_seed():
    return "call_auth_by_seed"


def patched_auth_by_wif():
    return "call_auth_by_wif"


def patched_auth_by_auth_file():
    return "call_auth_by_auth_file"


def patched_auth_by_scrypt():
    return "call_auth_by_scrypt"
