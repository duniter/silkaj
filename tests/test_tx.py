import pytest
from silkaj.tx import transaction_amount
from silkaj.money import UDValue


@pytest.mark.asyncio
async def test_transaction_amount():
    """test passed amounts passed tx command
    float ≠ 100 does not give the exact value"""

    assert await transaction_amount(141.89, None, None) == 14189
    assert await transaction_amount(141.99, None, None) == 14199
    assert await transaction_amount(141.01, None, None) == 14101

    ud_value = await UDValue().ud_value
    assert await transaction_amount(None, 1.1, None) == round(1.1 * ud_value)
    assert await transaction_amount(None, 1.9, None) == round(1.9 * ud_value)
    assert await transaction_amount(None, 1.0001, None) == round(1.0001 * ud_value)
    assert await transaction_amount(None, 9.9999, None) == round(9.9999 * ud_value)
