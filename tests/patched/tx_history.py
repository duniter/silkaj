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

from duniterpy.documents.transaction import Transaction

from patched.wot import pubkey_list
from patched.blockchain_tools import currency

fake_received_tx_hist = [
    {
        "version": 10,
        "locktime": 0,
        "blockstamp": "150574-000003D64BB3E107EEEF90922A60DB56A6DF14FB4415A3F4A852A87F889E1C31",
        "blockstampTime": 1535913486,
        "issuers": ["CvrMiUhAJpNyX5sdAyZqPE6yEFfSsf6j9EpMmeKvMCWW"],
        "inputs": [
            "7014:0:T:00DFBACFA3434057F6B2DAA8249324C64A658E40BC85CFD40E15FADDD88BACE3:1"
        ],
        "outputs": [
            "100:0:SIG(d88fPFbDdJXJANHH7hedFMaRyGcnVZj9c5cDaE76LRN)",
            "6914:0:SIG(CvrMiUhAJpNyX5sdAyZqPE6yEFfSsf6j9EpMmeKvMCWW)",
        ],
        "unlocks": ["0:SIG(0)"],
        "signatures": [
            "xz/l3o9GbUclrYDNKiRaVTrBP7cppDmrjDgE2rFNLJsnpu1e/AE2bHylftU09NYEDqzCUbehv19oF6zIRVwTDw=="
        ],
        "comment": "initialisation",
        "hash": "D2271075F2308C4092B1F57B3F1BE12AB684FAFCA62BA8EFE9F7F4D7A4D8D69F",
        "time": 111111114,
        "block_number": 150576,
        "received": None,
    },
    {
        "version": 10,
        "locktime": 0,
        "blockstamp": "400498-0000000EE3E7C41160E5638B7DB3F76A82068D6D3D1CC2332EE7A39AF43A9EA6",
        "blockstampTime": 1613798963,
        "issuers": ["CmFKubyqbmJWbhyH2eEPVSSs4H4NeXGDfrETzEnRFtPd"],
        "inputs": ["1023:0:D:CmFKubyqbmJWbhyH2eEPVSSs4H4NeXGDfrETzEnRFtPd:396949"],
        "outputs": [
            "100:0:SIG(d88fPFbDdJXJANHH7hedFMaRyGcnVZj9c5cDaE76LRN)",
            "923:0:SIG(CmFKubyqbmJWbhyH2eEPVSSs4H4NeXGDfrETzEnRFtPd)",
        ],
        "unlocks": ["0:SIG(0)"],
        "signatures": [
            "pYSOTCrl1QbsKrgjgNWnUfD3wJnpbalv9EwjAbZozTbTOSzYoj+UInzKS8/OiSdyVqFVDLdpewTD+FOHRENDAA=="
        ],
        "comment": "",
        "hash": "F1F2E6D6CF123AB78B98B662FE3AFDD2577B8F6CEBC245660B2E67BC9C2026F6",
        "time": 111111113,
        "block_number": 400500,
        "received": None,
    },
]


fake_sent_tx_hist = [
    {
        "version": 10,
        "locktime": 0,
        "blockstamp": "400503-0000000A7F3B6F4C5654D9CCFEA41E4726E02B08BB94EE30BD9A50908D28636D",
        "blockstampTime": 1613801234,
        "issuers": ["d88fPFbDdJXJANHH7hedFMaRyGcnVZj9c5cDaE76LRN"],
        "inputs": [
            "100:0:T:F1F2E6D6CF123AB78B98B662FE3AFDD2577B8F6CEBC245660B2E67BC9C2026F6:0"
        ],
        "outputs": ["100:0:SIG(CvrMiUhAJpNyX5sdAyZqPE6yEFfSsf6j9EpMmeKvMCWW)"],
        "unlocks": ["0:SIG(0)"],
        "signatures": [
            "cMNp7FF5yT/6LJT9CnNzkE08h+APEAYYwdFIROGxUZ9JGqbfPR1NRbcruq5Fl9BnBcJkuMNJbOwuYV8bPCmICw=="
        ],
        "comment": "",
        "hash": "580715ECD6743590F7A99A6C97E63511BC94B0293CB0037C6A3C96482F8DC7D2",
        "time": 111111112,
        "block_number": 400505,
        "received": None,
    },
    {
        "version": 10,
        "locktime": 0,
        "blockstamp": "400503-0000000A7F3B6F4C5654D9CCFEA41E4726E02B08BB94EE30BD9A50908D28636D",
        "blockstampTime": 1613801235,
        "issuers": ["d88fPFbDdJXJANHH7hedFMaRyGcnVZj9c5cDaE76LRN"],
        "inputs": [
            "100:0:T:D2271075F2308C4092B1F57B3F1BE12AB684FAFCA62BA8EFE9F7F4D7A4D8D69F:0"
        ],
        "outputs": ["100:0:SIG(CmFKubyqbmJWbhyH2eEPVSSs4H4NeXGDfrETzEnRFtPd)"],
        "unlocks": ["0:SIG(0)"],
        "signatures": [
            "WL3dRX4XUenWlDYYhRmEOUgL5+Tc08LlOJWHNjmTlxqtsdHhGn7MuQ3lK+3Xv7PV6VFEEdc3vlJ52pWCLKN5BA=="
        ],
        "comment": "",
        "hash": "E874CDAC01D9F291DC1E03F8B0ADB6C19259DE5A11FB73A16318BA1AD59B9EDC",
        "time": 111111111,
        "block_number": 400505,
        "received": None,
    },
]


async def patched_get_transactions_history(client, pubkey, received_txs, sent_txs):
    for received in fake_received_tx_hist:
        received_txs.append(Transaction.from_bma_history(currency, received))
    for sent in fake_sent_tx_hist:
        sent_txs.append(Transaction.from_bma_history(currency, sent))
