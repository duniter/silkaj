import pytest

from silkaj.tx import truncBase


@pytest.mark.parametrize('amount,base,expected', [
        (0, 0, 0),
        (10, 2, 0),
        (100, 2, 100),
        (306, 2, 300),
        (3060, 3, 3000),
])
def test_truncBase(amount, base, expected):
    assert truncBase(amount, base) == expected
