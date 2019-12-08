from subprocess import check_output


def test_info():
    """tests 'silkaj info' returns a number of members"""

    output = check_output(["silkaj", "info"])
    assert "Number of members" in output.decode()


def test_wot():
    """tests 'silkaj wot' returns a number of members"""

    output = check_output(["silkaj", "wot", "moul"]).decode()
    assert "moul (GfKER…) from block #0-E3B0C44298FC1…" in output
    assert "received_expire" in output
    assert "received" in output
    assert "sent" in output
    assert "sent_expire" in output


def test_id():
    """tests 'silkaj id' certification on gtest"""

    output = check_output(["silkaj", "--gtest", "id", "elois"]).decode()
    assert "D7CYHJXjaH4j7zRdWngUbsURPnSnjsCYtvo6f8dvW3C" in output


def test_amount():
    """tests 'silkaj amount' command on gtest"""

    output = check_output(
        ["silkaj", "--gtest", "balance", "3dnbnYY9i2bHMQUGyFp5GVvJ2wBkVpus31cDJA5cfRpj"]
    ).decode()
    assert "Total amount of: 3dnbnYY9i2bHMQUGyFp5GVvJ2wBkVpus31cDJA5cfRpj" in output
    assert "Total Relative     =" in output
    assert "UD ĞTest" in output
    assert "Total Quantitative =" in output
