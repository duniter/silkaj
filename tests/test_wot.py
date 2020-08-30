"""
Copyright  2016-2020 Maël Azimi <m.a@moul.re>

Silkaj is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Silkaj is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Silkaj. If not, see <https://www.gnu.org/licenses/>.
"""

import pytest
import click

from silkaj import wot


pubkey_titi_tata = "B4RoF48cTxzmsQDB3UjodKdZ2cVymKSKzgiPVRoMeA88"
pubkey_toto_tutu = "totoF48cTxzmsQDB3UjodKdZ2cVymKSKzgiPVRoMeA88"


def identity_card(uid, timestamp):
    return {
        "uid": uid,
        "meta": {"timestamp": timestamp},
    }


titi = identity_card(
    "titi",
    "590358-000156C5620946D1D63DAF82BF3AA735CE0B3518D59274171C88A7DBA4C906BC",
)
tata = identity_card(
    "tata",
    "210842-000000E7AAC79A07F487B33A48B3217F8A1F0A31CDB42C5DFC5220A20665B6B1",
)
toto = identity_card(
    "toto",
    "189601-0000011405B5C96EA69C1273370E956ED7887FA56A75E3EFDF81E866A2C49FD9",
)
tutu = identity_card(
    "tutu",
    "389601-0000023405B5C96EA69C1273370E956ED7887FA56A75E3EFDF81E866A2C49FD9",
)


async def patched_lookup_one(pubkey_uid):
    return [
        {
            "pubkey": pubkey_titi_tata,
            "uids": [titi],
            "signed": [],
        }
    ]


async def patched_lookup_two(pubkey_uid):
    return [
        {
            "pubkey": pubkey_titi_tata,
            "uids": [titi, tata],
            "signed": [],
        }
    ]


async def patched_lookup_three(pubkey_uid):
    return [
        {
            "pubkey": pubkey_titi_tata,
            "uids": [titi, tata],
            "signed": [],
        },
        {
            "pubkey": pubkey_toto_tutu,
            "uids": [toto],
            "signed": [],
        },
    ]


async def patched_lookup_four(pubkey_uid):
    return [
        {
            "pubkey": pubkey_titi_tata,
            "uids": [titi, tata],
            "signed": [],
        },
        {
            "pubkey": pubkey_toto_tutu,
            "uids": [toto, tutu],
            "signed": [],
        },
    ]


async def patched_lookup_five(pubkey_uid):
    return [
        {
            "pubkey": pubkey_titi_tata,
            "uids": [titi],
            "signed": [],
        },
        {
            "pubkey": pubkey_toto_tutu,
            "uids": [titi],
            "signed": [],
        },
    ]


def patched_prompt_titi(message):
    return "00"


def patched_prompt_tata(message):
    return "01"


def patched_prompt_toto(message):
    return "10"


def patched_prompt_tutu(message):
    return "11"


@pytest.mark.parametrize(
    "selected_uid, pubkey, patched_prompt, patched_lookup",
    [
        ("titi", pubkey_titi_tata, patched_prompt_titi, patched_lookup_one),
        ("tata", pubkey_titi_tata, patched_prompt_tata, patched_lookup_two),
        ("toto", pubkey_toto_tutu, patched_prompt_toto, patched_lookup_three),
        ("tutu", pubkey_toto_tutu, patched_prompt_tutu, patched_lookup_four),
        ("titi", pubkey_toto_tutu, patched_prompt_toto, patched_lookup_five),
    ],
)
@pytest.mark.asyncio
async def test_choose_identity(
    selected_uid, pubkey, patched_prompt, patched_lookup, capsys, monkeypatch
):
    monkeypatch.setattr(wot, "wot_lookup", patched_lookup)
    monkeypatch.setattr(click, "prompt", patched_prompt)
    identity_card, get_pubkey, signed = await wot.choose_identity(pubkey)
    assert pubkey == get_pubkey
    assert selected_uid == identity_card["uid"]

    # Check whether the table is not displayed in case of one identity
    # Check it is displayed for more than one identity
    # Check the uids and ids are in
    captured = capsys.readouterr()
    lookups = await patched_lookup("")

    # only one pubkey and one uid on this pubkey
    if len(lookups) == 1 and len(lookups[0]["uids"]) == 1:
        assert not captured.out

    # many pubkeys or many uid on one pubkey
    else:
        # if more than one pubkey, there should be a "10" numbering
        if len(lookups) > 1:
            assert " 10 " in captured.out
        for lookup in lookups:
            if len(lookup["uids"]) > 1:
                assert " 01 " in captured.out
            for uid in lookup["uids"]:
                assert uid["uid"] in captured.out
