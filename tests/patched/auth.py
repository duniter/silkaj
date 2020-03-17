# This file contains patches for auth functions.
from duniterpy.key import SigningKey


def patched_auth_method(uid):
    """
    insecure way to test keys
    """
    return SigningKey.from_credentials(uid, uid)


def patched_auth_by_seed():
    return "call_auth_by_seed"


def patched_auth_by_wif():
    return "call_auth_by_wif"


def patched_auth_by_auth_file():
    return "call_auth_by_auth_file"


def patched_auth_by_scrypt():
    return "call_auth_by_scrypt"
