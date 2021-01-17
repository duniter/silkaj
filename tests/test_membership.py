"""
Copyright  2016-2021 Maël Azimi <m.a@moul.re>

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

import sys
from unittest.mock import Mock
import pytest
from click.testing import CliRunner

from tabulate import tabulate
import pendulum

from duniterpy.documents import Membership, block_uid
from duniterpy.api import bma
from duniterpy.key import SigningKey

from patched.blockchain_tools import (
    currency,
    patched_params,
    patched_block,
    patched_head_block,
    fake_block_uid,
)
from patched.wot import (
    patched_wot_requirements_one_pending,
    patched_wot_requirements_no_pending,
)

from silkaj import auth, wot
from silkaj.cli import cli
from silkaj.network_tools import ClientInstance
from silkaj import membership
from silkaj.blockchain_tools import BlockchainParams, HeadBlock
from silkaj.constants import (
    SUCCESS_EXIT_STATUS,
    FAILURE_EXIT_STATUS,
)
from silkaj.tui import display_pubkey_and_checksum

# AsyncMock available from Python 3.8. asynctest is used for Py < 3.8
if sys.version_info[1] > 7:
    from unittest.mock import AsyncMock
else:
    from asynctest.mock import CoroutineMock as AsyncMock


# Values and patches
pubkey = "EA7Dsw39ShZg4SpURsrgMaMqrweJPUFPYHwZA8e92e3D"
identity_timestamp = block_uid(
    "0-E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
)
identity_uid = "toto"
membership_timestamp = fake_block_uid


def patched_auth_method():
    return SigningKey.from_credentials(identity_uid, identity_uid)


async def patched_choose_identity(pubkey):
    return (
        {"uid": identity_uid, "meta": {"timestamp": identity_timestamp}},
        pubkey,
        None,
    )


@pytest.mark.parametrize(
    "dry_run, confirmation, exit_code",
    [
        (True, True, SUCCESS_EXIT_STATUS),
        (False, False, SUCCESS_EXIT_STATUS),
        (False, True, FAILURE_EXIT_STATUS),
    ],
)
def test_membership_cmd(dry_run, confirmation, exit_code, monkeypatch):
    # Monkeypatch and Mock
    monkeypatch.setattr(auth, "auth_method", patched_auth_method)
    monkeypatch.setattr(HeadBlock, "get_head", patched_head_block)
    monkeypatch.setattr(wot, "choose_identity", patched_choose_identity)

    patched_display_confirmation_table = AsyncMock()
    monkeypatch.setattr(
        membership,
        "display_confirmation_table",
        patched_display_confirmation_table,
    )
    if not dry_run:
        patched_generate_membership_document = Mock()
        monkeypatch.setattr(
            membership,
            "generate_membership_document",
            patched_generate_membership_document,
        )

    # Run membership command
    command = ["membership"]
    if dry_run:
        command += ["--dry-run"]
    confirmations = "No\nYes\nYes" if confirmation else "No\nYes\nNo"
    result = CliRunner().invoke(cli, args=command, input=confirmations)

    # Assert functions are called
    patched_display_confirmation_table.assert_awaited_once_with(
        identity_uid,
        pubkey,
        identity_timestamp,
    )
    if not dry_run and confirmation:
        patched_generate_membership_document.assert_called_with(
            currency,
            pubkey,
            membership_timestamp,
            identity_uid,
            identity_timestamp,
        )
    if dry_run:
        assert "Type: Membership" in result.output

    assert result.exit_code == exit_code


@pytest.mark.parametrize(
    "patched_wot_requirements",
    [patched_wot_requirements_no_pending, patched_wot_requirements_one_pending],
)
@pytest.mark.asyncio
async def test_display_confirmation_table(
    patched_wot_requirements, monkeypatch, capsys
):
    monkeypatch.setattr(bma.wot, "requirements", patched_wot_requirements)
    monkeypatch.setattr(bma.blockchain, "parameters", patched_params)
    monkeypatch.setattr(bma.blockchain, "block", patched_block)

    client = ClientInstance().client
    identities_requirements = await client(bma.wot.requirements, pubkey)
    for identity_requirements in identities_requirements["identities"]:
        if identity_requirements["uid"] == identity_uid:
            membership_expires = identity_requirements["membershipExpiresIn"]
            pending_expires = identity_requirements["membershipPendingExpiresIn"]
            pending_memberships = identity_requirements["pendingMemberships"]
            break

    table = list()
    if membership_expires:
        expires = pendulum.now().add(seconds=membership_expires).diff_for_humans()
        table.append(["Expiration date of current membership", expires])

    if pending_memberships:
        line = [
            "Number of pending membership(s) in the mempool",
            len(pending_memberships),
        ]
        table.append(line)
        expiration = pendulum.now().add(seconds=pending_expires).diff_for_humans()
        table.append(["Pending membership documents will expire", expiration])

    table.append(["User Identifier (UID)", identity_uid])
    table.append(["Public Key", display_pubkey_and_checksum(pubkey)])

    table.append(["Block Identity", str(identity_timestamp)[:45] + "…"])

    block = await client(bma.blockchain.block, identity_timestamp.number)
    table.append(
        ["Identity published", pendulum.from_timestamp(block["time"]).format("LL")],
    )

    params = await BlockchainParams().params
    membership_validity = (
        pendulum.now().add(seconds=params["msValidity"]).diff_for_humans()
    )
    table.append(["Expiration date of new membership", membership_validity])

    membership_mempool = (
        pendulum.now().add(seconds=params["msPeriod"]).diff_for_humans()
    )
    table.append(
        ["Expiration date of new membership from the mempool", membership_mempool]
    )

    expected = tabulate(table, tablefmt="fancy_grid") + "\n"

    await membership.display_confirmation_table(
        identity_uid, pubkey, identity_timestamp
    )
    captured = capsys.readouterr()
    assert expected == captured.out


def test_generate_membership_document():
    generated_membership = membership.generate_membership_document(
        currency,
        pubkey,
        membership_timestamp,
        identity_uid,
        identity_timestamp,
    )
    expected = Membership(
        version=10,
        currency=currency,
        issuer=pubkey,
        membership_ts=membership_timestamp,
        membership_type="IN",
        uid=identity_uid,
        identity_ts=identity_timestamp,
    )
    # Direct equality check can be done without raw() once Membership.__eq__() is implemented
    assert expected.raw() == generated_membership.raw()
