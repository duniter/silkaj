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

from silkaj.network_tools import ClientInstance
from duniterpy.api.bma import blockchain


class BlockchainParams(object):
    __instance = None

    def __new__(cls):
        if BlockchainParams.__instance is None:
            BlockchainParams.__instance = object.__new__(cls)
        return BlockchainParams.__instance

    def __init__(self):
        self.params = self.get_params()

    async def get_params(self):
        client = ClientInstance().client
        return await client(blockchain.parameters)


class HeadBlock(object):
    __instance = None

    def __new__(cls):
        if HeadBlock.__instance is None:
            HeadBlock.__instance = object.__new__(cls)
        return HeadBlock.__instance

    def __init__(self):
        self.head_block = self.get_head()

    async def get_head(self):
        client = ClientInstance().client
        return await client(blockchain.current)
