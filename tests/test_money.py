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

import duniterpy.api.bma.tx as bma_tx

# had to import from wot to prevent loop dependencies
from silkaj.wot import display_pubkey_and_checksum
from silkaj.cli import cli
from silkaj.constants import FAILURE_EXIT_STATUS
from silkaj.money import get_sources


@pytest.mark.asyncio
async def test_get_sources(monkeypatch):
    """
    test that get_source() will :
      * only use simple SIG txs
      * only use blockchain sources to compute balance
      * return pending txs in first positions of the sources list
    """

    async def patched_tx_sources(self, pubkey):
        return {
            "currency": "g1-test",
            "pubkey": "AhRMHUxMPXSeG7qXZrE6qCdjwK9p2bu5Eqei7xAWVEDK",
            "sources": [
                # this source will be returned in inputlist, and its amount used.
                {
                    "type": "T",
                    "noffset": 2,
                    "identifier": "0310F56D22F4CEF5E41B9D5CACB6E21F224B79D9398D53A4E754866435710242",
                    "amount": 10,
                    "base": 3,
                    "conditions": "SIG(AhRMHUxMPXSeG7qXZrE6qCdjwK9p2bu5Eqei7xAWVEDK)",
                },
                # this source will not be returned (complex unlock condition)
                {
                    "type": "T",
                    "noffset": 3,
                    "identifier": "0D6A29451E64F468C0DB19F70D0D17F65BDCC98F3A16DD55B3755BE124B3DD6C",
                    "amount": 30,
                    "base": 3,
                    "conditions": "(SIG(2VgEZnrGQ5hEgwoNrcXZnD9c8o5jL63LPBmJdvMyFhGe) || (SIG(AhRMHUxMPXSeG7qXZrE6qCdjwK9p2bu5Eqei7xAWVEDK) && CSV(864)))",
                },
            ],
        }

    async def patched_tx_pending(self, pubkey):
        return {
            "currency": "g1-test",
            "pubkey": "AhRMHUxMPXSeG7qXZrE6qCdjwK9p2bu5Eqei7xAWVEDK",
            "history": {
                "sending": [],
                "received": [],
                "receiving": [],
                "sent": [],
                "pending": [
                    {
                        "version": 10,
                        "locktime": 0,
                        "blockstamp": "671977-000008B6DE75715D3D83450A957CD75F781DA8E3E8E966D42A02F59049209533",
                        "blockstampTime": 1607363853,
                        "issuers": ["6upqFiJ66WV6N3bPc8x8y7rXT3syqKRmwnVyunCtEj7o"],
                        "inputs": [
                            "2739:3:D:6upqFiJ66WV6N3bPc8x8y7rXT3syqKRmwnVyunCtEj7o:664106"
                        ],
                        "outputs": [
                            "60:3:SIG(AhRMHUxMPXSeG7qXZrE6qCdjwK9p2bu5Eqei7xAWVEDK)",
                            "2679:3:SIG(6upqFiJ66WV6N3bPc8x8y7rXT3syqKRmwnVyunCtEj7o)",
                        ],
                        "unlocks": ["0:SIG(0)"],
                        "signatures": [
                            "lrmzr/RkecJBOczlmkp3BNCiXejBzTnHdqmNzxQJyJDIx0UHON4jYkqVKeD77+nrOl8jVtonLt3ZYqd1fhi1Cw=="
                        ],
                        "comment": "DEMAIN DES L_AUBE",
                        "hash": "D5A1A1AAA43FAA242CC2B19763619DA625092BB7FD23397AD362215375A920C8",
                        "time": None,
                        "block_number": None,
                        "received": None,
                    }
                ],
            },
        }

    monkeypatch.setattr(bma_tx, "sources", patched_tx_sources)
    monkeypatch.setattr(bma_tx, "pending", patched_tx_pending)

    listinput, balance = await get_sources(
        "AhRMHUxMPXSeG7qXZrE6qCdjwK9p2bu5Eqei7xAWVEDK"
    )
    assert len(listinput) == 2
    # test SIG() only source is used
    assert balance == 10000  # 10 in unitbase 3
    assert (
        listinput[0].origin_id
        == "D5A1A1AAA43FAA242CC2B19763619DA625092BB7FD23397AD362215375A920C8"
    )


def test_balance_errors():
    """
    test balance command errors
    """

    # twice the same pubkey
    result = CliRunner().invoke(
        cli,
        [
            "balance",
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
            "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh",
        ],
    )
    pubkeyCk = display_pubkey_and_checksum(
        "BFb5yv8z1fowR6Z8mBXTALy5z7gHfMU976WtXhmRsUMh"
    )
    assert f"ERROR: pubkey {pubkeyCk} was specified many times" in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS

    # wrong pubkey
    result = CliRunner().invoke(
        cli,
        [
            "balance",
            "B",
        ],
    )
    assert "ERROR: pubkey B has a wrong format" in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS

    # no pubkey
    result = CliRunner().invoke(cli, ["balance"])
    assert "You should specify one or many pubkeys" in result.output
    assert result.exit_code == FAILURE_EXIT_STATUS
