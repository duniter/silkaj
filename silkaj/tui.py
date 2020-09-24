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

from datetime import datetime

from silkaj import wot
from silkaj import crypto_tools as ct
from silkaj.constants import SHORT_PUBKEY_SIZE


def display_amount(tx, message, amount, ud_value, currency_symbol):
    """
    Displays an amount in unit and relative reference.
    """
    amount_UD = round((amount / ud_value), 2)
    tx.append(
        [
            message + " (unit|relative)",
            "{unit_amount} {currency_symbol} | {UD_amount} UD {currency_symbol}".format(
                unit_amount=str(amount / 100),
                currency_symbol=currency_symbol,
                UD_amount=str(amount_UD),
            ),
        ]
    )


async def display_pubkey(tx, message, pubkey):
    """
    Displays a pubkey and the eventually associated id.
    """
    tx.append([message + " (pubkey:checksum)", display_pubkey_and_checksum(pubkey)])
    id = await wot.is_member(pubkey)
    if id:
        tx.append([message + " (id)", id["uid"]])


def display_pubkey_and_checksum(pubkey, short=False, length=SHORT_PUBKEY_SIZE):
    """
    Returns "<pubkey>:<checksum>" in full form.
    returns `length` first chars of pubkey and checksum in short form.
    `length` defaults to SHORT_PUBKEY_SIZE.
    """
    short_pubkey = pubkey[:length] + "…" if short else pubkey
    return short_pubkey + ":" + ct.gen_checksum(pubkey)


def convert_time(timestamp, kind):
    ts = int(timestamp)
    date = "%Y-%m-%d"
    hour = "%H:%M"
    second = ":%S"
    if kind == "all":
        pattern = date + " " + hour + second
    elif kind == "date":
        pattern = date
    elif kind == "hour":
        pattern = hour
        if ts >= 3600:
            pattern += second
    return datetime.fromtimestamp(ts).strftime(pattern)
