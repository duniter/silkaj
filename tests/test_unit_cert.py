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

from unittest.mock import patch

from silkaj.cert import certification_confirmation


# @patch('builtins.input')
# def test_certification_confirmation(mock_input):
#    id_to_certify = {"pubkey": "pubkeyid to certify"}
#    main_id_to_certify = {"uid": "id to certify"}
#    mock_input.return_value = "yes"
#
#    assert certification_confirmation(
#        "certifier id",
#        "certifier pubkey",
#        id_to_certify,
#        main_id_to_certify)
#
#    mock_input.assert_called_once()
#
#
# @patch('builtins.input')
# def test_certification_confirmation_no(mock_input):
#    id_to_certify = {"pubkey": "pubkeyid to certify"}
#    main_id_to_certify = {"uid": "id to certify"}
#    mock_input.return_value = "no"
#
#    assert certification_confirmation(
#        "certifier id",
#        "certifier pubkey",
#        id_to_certify,
#        main_id_to_certify) is None
#
#    mock_input.assert_called_once()
