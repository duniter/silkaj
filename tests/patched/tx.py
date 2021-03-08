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

from duniterpy.key import SigningKey
from silkaj.tools import message_exit


async def patched_transaction_confirmation(
    issuer_pubkey,
    pubkey_amount,
    tx_amounts,
    outputAddresses,
    outputBackChange,
    comment,
):
    if not (
        (
            isinstance(issuer_pubkey, str)
            and isinstance(pubkey_amount, int)
            and isinstance(tx_amounts, list)
            and isinstance(outputAddresses, list)
            and isinstance(comment, str)
            and isinstance(outputBackchange, str)
        )
        and len(tx_amounts) == len(outputAddresses)
        and sum(tx_amounts) <= pubkey_amount
    ):
        message_exit(
            "Test error : patched_transaction_confirmation() : Parameters are not coherent"
        )


async def patched_handle_intermediaries_transactions(
    key,
    issuers,
    tx_amounts,
    outputAddresses,
    Comment="",
    OutputbackChange=None,
):
    if not (
        (
            isinstance(key, SigningKey)
            and isinstance(issuers, str)
            and isinstance(tx_amounts, list)
            and isinstance(outputAddresses, list)
            and isinstance(Comment, str)
            and (isinstance(OutputBackchange, str) or OutputbackChange == None)
        )
        and len(tx_amounts) == len(outputAddresses)
        and key.pubkey() == issuers
    ):
        message_exit(
            "Test error : patched_handle_intermediaries_transactions() : Parameters are not coherent"
        )


async def patched_generate_and_send_transaction(
    key,
    issuers,
    tx_amounts,
    listinput_and_amount,
    outputAddresses,
    Comment,
    OutputbackChange,
):
    if not (
        (
            isinstance(key, SigningKey)
            and isinstance(issuers, str)
            and isinstance(tx_amounts, list)
            and isinstance(listinput_and_amount, tuple)
            and isinstance(outputAddresses, list)
            and isinstance(Comment, str)
            and isinstance(OutputBackchange, str)
        )
        and len(tx_amounts) == len(outputAddresses)
        and sum(tx_amounts) <= listinput_and_amount[2]
        and key.pubkey() == issuers
    ):
        message_exit(
            "Test error : patched_generate_and_send_transaction() : Parameters are not coherent"
        )
    pass
