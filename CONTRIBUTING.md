# Contributing

## Goals
Part of the Duniter project running the Ğ1 currency, Silkaj project is aiming to create a generic tool to manage his account and wallets, and to monitor the currency.

## Install the development environement
We are using [Poetry](https://poetry.eustace.io/) as a development environement solution. Start [installing Poetry](install_poetry.md).
This will install a sandboxed Python environement.
Dependencies will be installed in it in order to have Silkaj running and to have pre-installed developement tools.

## Workflow
- We use branches for merge requests
- We prefer fast-forward and rebase method than having a merge commit. This in order to have a clean history.

## Branches
- `master` branch as stable
- maintainance branches, to maintain a stable version while developing future version with breaking changes. For instance: `0.7`
- `dev` branch

## Developing with DuniterPy
[DuniterPy](https://git.duniter.org/clients/python/duniterpy) is a Python library for Duniter clients.
It implements a client with multiple APIs, the handling for document signing.
As it is coupled with Silkaj, it is oftenly needed to develop in both repositories.

### How to use DuniterPy as editable with Poetry
Clone DuniterPy locally alongside of `silkaj` repository:

```bash
silkaj> cd ..
git clone https://git.duniter.org/clients/python/duniterpy
```

Use DuniterPy as a [path dependency](https://poetry.eustace.io/docs/versions/#path-dependencies):
```bash
poetry add ../duniterpy
```

## Formatting
We are using [Black](https://github.com/python/black) as a formatter tool.

Black is not in the development dependencies in order to keep Python 3.5 support.
There is three way you can install Black:
- From your package manager. i.e. Debian Buster: `sudo apt install black`
- On your machine via `pip`: `pip3 install black --user`
- In your Poetry virtualenv:
To have it installed in your Poetry virtualenv, you need Python v3.6 or greater.
In the `pyproject.toml` pass the Python requirement version from "3.5.x" to "3.6".
Then, install it with `poetry add black --dev`.

Once installed in your development environement, run Black on a Python file to format it:
```bash
poetry run black silkaj/cli.py
```

### Pre-commit
Then, you can use the `pre-commit` tool to check staged changes before committing.
To do so, you need to run `pre-commit install` to install the git hook.
Black is called on staged files, so commit should fail in case black made changes.
You will have to add Black changes in order to commit your changes.

## Tests
We are using [Pytest](https://pytest.org) as a tests framework. To know more about how Silkaj implement it read the [project test documentation](test_and_coverage.md).

To run tests, within `silkaj` repository:
```bash
poetry run pytest
```

### How to test a single file
Specifiy the path of the test:
```bash
poetry run pytest tests/test_end_to_end.py
```

## Version update
We are using the [Semantic Versioning](https://semver.org).

To create a release, we use following script which will update the version in different files, and will make a commit and a tag out of it.
```bash
./release.sh 0.8.1
```

Then, a `git push --tags` is necessary to publish the tag. Git could be configured to publish tags with a simple `push`.

## PyPI and PyPI test distributions
Silkaj is distributed to PyPI, the Python Package Index, for further `pip` installation.
Silkaj can be published to [PyPI](https://pypi.org/project/silkaj) or to [PyPI test](https://test.pypi.org/project/silkaj/) for testing purposes.
Publishing to PyPI or PyPI test can be directly done from the continuous delivery or from Poetry it-self.
The CD jobs does appear on a tag and have to be triggered manually.
Only the project maintainers have the rights to publish tags.

### PyPI
Publishing to PyPI from Poetry:
```bash
poetry publish --build
```
### PyPI test
Publishing to PyPI test from Poetry:
```bash
poetry config repositories.pypi_test https://test.pypi.org/legacy/
poetry publish --build --repository pypi_test
```

To install this package:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.python.org/simple/ silkaj
```

The `--extra-index-url` is used to retrieve dependencies packages from the official PyPI not to get issues with missing or testing dependencies comming from PyPI test repositories.

## Continuous integration and delivery
### Own built Docker images
- https://git.duniter.org/docker/python3/poetry
- Python images based on Debian Buster
- Poetry installed on top
- Black installed on v3.8

### Jobs
- Checks:
  - Format
  - Build
- Tests on supported Python versions:
  - Installation
  - Pytest for v3.5, 3.6, 3.7, and 3.8
- PyPI distribution
  - test
  - stable
