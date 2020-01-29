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
from click.testing import CliRunner

from duniterpy.documents import Block
from duniterpy.api.client import Client
from duniterpy.api import bma

from silkaj.network_tools import EndPoint
from silkaj.blocks import (
    verify_blocks_signatures,
    check_passed_blocks_range,
    get_chunk_size,
    get_chunk,
    verify_block_signature,
    display_result,
)
from silkaj.constants import (
    SUCCESS_EXIT_STATUS,
    FAILURE_EXIT_STATUS,
    BMA_MAX_BLOCKS_CHUNK_SIZE,
)


G1_INVALID_BLOCK_SIG = 15144
HEAD_BLOCK = 48000


async def current(self):
    return {"number": HEAD_BLOCK}


@pytest.mark.parametrize(
    "from_block, to_block", [(2, 1), (20000, 15000), (0, HEAD_BLOCK + 1), (300000, 0)]
)
@pytest.mark.asyncio
async def test_check_passed_blocks_range(from_block, to_block, capsys, monkeypatch):
    monkeypatch.setattr("duniterpy.api.bma.blockchain.current", current)
    client = Client(EndPoint().BMA_ENDPOINT)
    # https://medium.com/python-pandemonium/testing-sys-exit-with-pytest-10c6e5f7726f
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        await check_passed_blocks_range(client, from_block, to_block)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == FAILURE_EXIT_STATUS
    captured = capsys.readouterr()
    if to_block == HEAD_BLOCK + 1:
        expected = "Passed TO_BLOCK argument is bigger than the head block: " + str(
            HEAD_BLOCK
        )
    else:
        expected = "TO_BLOCK should be bigger or equal to FROM_BLOCK\n"
    assert expected in captured.out


@pytest.mark.parametrize(
    "from_block, to_block",
    [
        (G1_INVALID_BLOCK_SIG, G1_INVALID_BLOCK_SIG),
        (G1_INVALID_BLOCK_SIG - 5, G1_INVALID_BLOCK_SIG + 5),
        (1, 10),
        (HEAD_BLOCK - 1, 0),
    ],
)
def test_verify_blocks_signatures(from_block, to_block, monkeypatch):
    monkeypatch.setattr("duniterpy.api.bma.blockchain.current", current)
    blocks_range = [str(from_block), str(to_block)]
    result = CliRunner().invoke(verify_blocks_signatures, blocks_range)
    assert result.exit_code == SUCCESS_EXIT_STATUS
    if to_block == 0:
        to_block = HEAD_BLOCK
    expected = "Within {0}-{1} range, ".format(from_block, to_block)
    if from_block == 1 or from_block == HEAD_BLOCK - 1:
        expected += "no blocks with a wrong signature."
    else:
        expected += "blocks with a wrong signature: " + str(G1_INVALID_BLOCK_SIG)
    assert expected + "\n" in result.output


@pytest.mark.parametrize(
    "from_block, to_block, chunks_from, chunk_from",
    [
        (140, 15150, [140, 5140, 10140, 15140], 140),
        (140, 15150, [140, 5140, 10140, 15140], 15140),
        (0, 2, [0], 0),
    ],
)
def test_get_chunk_size(from_block, to_block, chunks_from, chunk_from):
    chunk_size = get_chunk_size(from_block, to_block, chunks_from, chunk_from)
    if chunk_from != chunks_from[-1]:
        assert chunk_size == BMA_MAX_BLOCKS_CHUNK_SIZE
    else:
        assert chunk_size == to_block + 1 - chunk_from


@pytest.mark.parametrize("chunk_size, chunk_from", [(2, 1), (5, 10)])
@pytest.mark.asyncio
async def test_get_chunks(chunk_size, chunk_from):
    client = Client(EndPoint().BMA_ENDPOINT)
    chunk = await get_chunk(client, chunk_size, chunk_from)
    assert chunk[0]["number"] + chunk_size - 1 == chunk[-1]["number"]
    await client.close()


invalid_signature = "fJusVDRJA8akPse/sv4uK8ekUuvTGj1OoKYVdMQQAACs7OawDfpsV6cEMPcXxrQTCTRMrTN/rRrl20hN5zC9DQ=="
invalid_block_raw = "Version: 10\nType: Block\nCurrency: g1\nNumber: 15144\nPoWMin: 80\n\
Time: 1493683741\nMedianTime: 1493681008\nUnitBase: 0\n\
Issuer: D9D2zaJoWYWveii1JRYLVK3J4Z7ZH3QczoKrnQeiM6mx\nIssuersFrame: 106\n\
IssuersFrameVar: 0\nDifferentIssuersCount: 21\n\
PreviousHash: 0000033D8562368F1B099E924A4A83119BDA0452FAB2A8A4F1B1BA11F5450597\n\
PreviousIssuer: 5WD4WSHE96ySreSwQFXPqaKaKcwboRNApiPHjPWB6V9C\nMembersCount: 98\n\
Identities:\nJoiners:\nActives:\nLeavers:\nRevoked:\nExcluded:\nCertifications:\n\
Transactions:\nInnerHash: 8B194B5C38CF0A38D16256405AC3E5FA5C2ABD26BE4DCC0C7ED5CC9824E6155B\n\
Nonce: 30400000119992\n"

valid_signature = "qhXtFtl6A/ZL7JMb7guSDlxiISGsHkQ4hTz5mhhdZO0KCLqD2TmvjcGpUFETBSdRYVacvFYOvUANyevlcfx6Ag=="
valid_block_raw = "Version: 11\nType: Block\nCurrency: g1-test\nNumber: 509002\n\
PoWMin: 60\nTime: 1580293955\nMedianTime: 1580292050\nUnitBase: 2\n\
Issuer: 5B8iMAzq1dNmFe3ZxFTBQkqhq4fsztg1gZvxHXCk1XYH\nIssuersFrame: 26\n\
IssuersFrameVar: 0\nDifferentIssuersCount: 5\n\
PreviousHash: 0000EC4030E92E85F22F32663F5ABE137BA01CE59AF2A96050877320174C4A90\n\
PreviousIssuer: Dz37iRAXeg4nUsfVH82m61b39HK5fqm6Bu7mM2ujLYz1\nMembersCount: 11\n\
Identities:\nJoiners:\nActives:\nLeavers:\nRevoked:\nExcluded:\nCertifications:\n\
Transactions:\nInnerHash: 19A53ABFA19EC77B6360E38EA98BE10154CB92307F4909AE49E786CA7149F8C6\n\
Nonce: 10099900003511\n"


@pytest.mark.parametrize(
    "signature, block_raw",
    [(invalid_signature, invalid_block_raw), (valid_signature, valid_block_raw)],
)
def test_verify_block_signature(signature, block_raw):
    # Check with valid and non-valid signatures block
    invalid_signatures_blocks = []
    block = Block.from_signed_raw(block_raw + signature + "\n")
    verify_block_signature(invalid_signatures_blocks, block)
    if block.number == G1_INVALID_BLOCK_SIG:
        assert invalid_signatures_blocks == [block.number]
    else:
        assert invalid_signatures_blocks == []


@pytest.mark.parametrize(
    "from_block, to_block, invalid_blocks_signatures",
    [(0, 5, []), (100, 500, [53]), (470, 2341, [243, 453])],
)
def test_display_result(from_block, to_block, invalid_blocks_signatures, capsys):
    expected = "Within {0}-{1} range, ".format(from_block, to_block)
    if invalid_blocks_signatures:
        expected += "blocks with a wrong signature: "
        expected += " ".join(str(n) for n in invalid_blocks_signatures)
    else:
        expected += "no blocks with a wrong signature."
    display_result(from_block, to_block, invalid_blocks_signatures)
    captured = capsys.readouterr()
    assert expected + "\n" == captured.out
