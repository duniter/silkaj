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
