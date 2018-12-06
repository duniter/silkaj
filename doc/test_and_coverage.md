## Test and coverage

### Install tests dependencies

Using pipenv:
```
pipenv install --dev
```

### Runing tests:

Simply run:
```
pytest
```

To have a coverage report:
```
pytest --cov silkaj --cov-report html:cov_html
```

Where: 
* `--cov silkaj` option generates coverage data on the silkaj package
* `--cov-report html:cov_html` generates a browsable report of coverage in cov\_html dir. You can omit this if you just want coverage data to be generated

See [pytest documentation](https://docs.pytest.org/en/latest/usage.html) for more information


### Writing tests

There should be 3 kinds of test:
* end to end test: uses the real data and the real blockchain. Obviously don't presume the data value as it can change. These test are written in tests/test\_end\_to\_end.py.
* integration test: mock some of the input and/or output classes and shouldn't use the actual blockchain, you should use this when mocking a class (used by your code) is too complicated.
* unit test: for functions that don't need mock or mock can me done easily (you should prefer this to integration tests). Are written in tests/test\_unit\_*package*.py

You should try to write an end to end test first, then if your coverage too bad add some unit tests. If it's still too bad, write an integration test.

A better strategy (TDD) is to write first the End to end test. When it fails, before writing the code, you should implement the unit tests. When this one fails too, you can write your code to make your test pass. It's better but takes longer and the code is tested at least twice. So the previous strategy is a better compromise

### Tips

Test an Exception is raised: https://docs.pytest.org/en/latest/assert.html#assertions-about-expected-exceptions

Test a function with several values: You can use pytest.mark.parametrize as done in tests/test\_unit\_tx.py

To mock a user input:

```python
from unittest.mock import patch

from silkaj.cert import certification_confirmation


# this will add a mock_input parameter that will be used whenever the code tries to get input from user
@patch('builtins.input')
def test_certification_confirmation(mock_input):
    id_to_certify = {"pubkey": "pubkeyid to certify"}
    main_id_to_certify = {"uid": "id to certify"}

    # the input will return "yes" to the tested function (certification_confirmation)
    mock_input.return_value = "yes"

    # ensure the tested function returns something
    assert certification_confirmation(
        "certifier id",
        "certifier pubkey",
        id_to_certify,
        main_id_to_certify)

    # ensure that input is called once
    mock_input.assert_called_once()
```
