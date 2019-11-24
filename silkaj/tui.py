"""
Copyright  2016-2019 Maël Azimi <m.a@moul.re>

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

from silkaj import wot


def display_amount(tx, message, amount, ud_value, currency_symbol):
    """
    Displays an amount in unit and relative reference.
    """
    amount_UD = round((amount / ud_value), 4)
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
    tx.append([message + " (pubkey)", pubkey])
    id = await wot.is_member(pubkey)
    if id:
        tx.append([message + " (id)", id["uid"]])
