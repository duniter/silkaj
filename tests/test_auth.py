import pytest
import click

from silkaj import auth

from patched.auth import (
    patched_auth_by_seed,
    patched_auth_by_wif,
    patched_auth_by_auth_file,
    patched_auth_by_scrypt,
)

# test auth_method
@pytest.mark.parametrize(
    "seed, file, wif, auth_method_called",
    [
        (True, False, False, "call_auth_by_seed"),
        (False, True, False, "call_auth_by_auth_file"),
        (False, False, True, "call_auth_by_wif"),
        (False, False, False, "call_auth_by_scrypt"),
    ],
)
def test_auth_method(seed, file, wif, auth_method_called, monkeypatch):
    monkeypatch.setattr("silkaj.auth.auth_by_seed", patched_auth_by_seed)
    monkeypatch.setattr("silkaj.auth.auth_by_wif", patched_auth_by_wif)
    monkeypatch.setattr("silkaj.auth.auth_by_auth_file", patched_auth_by_auth_file)
    monkeypatch.setattr("silkaj.auth.auth_by_scrypt", patched_auth_by_scrypt)
    ctx = click.Context(
        click.Command(""), obj={"AUTH_SEED": seed, "AUTH_FILE": file, "AUTH_WIF": wif}
    )
    with ctx:
        assert auth_method_called == auth.auth_method()
