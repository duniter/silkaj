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

import pytest
from silkaj import network_tools


@pytest.mark.parametrize(
    "address,type",
    [
        ("test.domain.com", 0),
        ("8.8.8.8", 4),
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", 6),
        ("2001:db8::1:0", 6),
        ("2001:0db8:0t00:0000:0000:ff00:0042:8329", 0),
    ],
)
def test_check_ip(address, type):
    assert network_tools.check_ip(address) == type
