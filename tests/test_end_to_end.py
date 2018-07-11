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
