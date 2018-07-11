from subprocess import check_output


def test_info():
    """tests './silkaj info' returns a number of members"""

    output = check_output(["silkaj", "info"])
    assert "Number of members" in output.decode()
