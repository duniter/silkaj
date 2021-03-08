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

# This file contains fake values for testing purposes

from duniterpy.documents.block_uid import BlockUID

currency = "g1"

mocked_block = {
    "number": 48000,
    "time": 1592243760,
    "unitbase": 0,
    "currency": currency,
    "hash": "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C",
}

fake_block_uid = BlockUID(
    48000, "0000010D30B1284D34123E036B7BE0A449AE9F2B928A77D7D20E3BDEAC7EE14C"
)


async def patched_params(self):
    return {
        "msValidity": 31557600,
        "msPeriod": 5259600,
    }


async def patched_block(self, number):
    return mocked_block


## mock head_block()
async def patched_head_block(self):
    return mocked_block
