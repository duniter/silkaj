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

pubkey_list = [
    {"pubkey": "9cwBBgXcSVMT74xiKYygX6FM5yTdwd3NABj1CfHbbAmp", "uid": ""},
    {"pubkey": "BUhLyJT17bzDVXW66xxfk1F7947vytmwJVadTaWb8sJS", "uid": ""},
    {"pubkey": "CtM5RZHopnSRAAoWNgTWrUhDEmspcCAxn6fuCEWDWudp", "uid": "riri"},
    {"pubkey": "HcRgKh4LwbQVYuAc3xAdCynYXpKoiPE6qdxCMa8JeHat", "uid": "fifi"},
    {"pubkey": "2sq4w8yYVDWNxVWZqGWWDriFf5z7dn7iLahDCvEEotuY", "uid": "loulou"},
]


# mock is_member
async def patched_is_member(pubkey):
    for account in pubkey_list:
        if account["pubkey"] == pubkey:
            if account["uid"]:
                return account
    return False


# patch wot requirements
async def patched_wot_requirements_one_pending(pubkey, identity_uid):
    return {
        "identities": [
            {
                "uid": "toto",
                "pendingMemberships": [
                    {
                        "membership": "IN",
                        "issuer": "5B8iMAzq1dNmFe3ZxFTBQkqhq4fsztg1gZvxHXCk1XYH",
                        "number": 613206,
                        "blockNumber": 613206,
                        "userid": "moul-test",
                        "expires_on": 1598624404,
                        "type": "IN",
                    }
                ],
                "membershipPendingExpiresIn": 6311520,
                "membershipExpiresIn": 2603791,
            },
        ],
    }


async def patched_wot_requirements_no_pending(pubkey, identity_uid):
    return {
        "identities": [
            {
                "uid": "toto",
                "pendingMemberships": [],
                "membershipPendingExpiresIn": 0,
                "membershipExpiresIn": 3724115,
            }
        ]
    }
