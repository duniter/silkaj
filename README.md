# Silkaj
[![Version](https://img.shields.io/pypi/v/silkaj.svg)](https://pypi.python.org/pypi/silkaj) [![License](https://img.shields.io/pypi/l/silkaj.svg)](https://pypi.python.org/pypi/silkaj) [![Python versions](https://img.shields.io/pypi/pyversions/silkaj.svg)](https://pypi.python.org/pypi/silkaj)

- CLI Duniter client written with Python 3.
- [Website](https://silkaj.duniter.org)

## Install
```bash
pip3 install silkaj --user
```

- [Install with Pip](doc/install_pip.md)
- [Install with pipenv](doc/install_pipenv.md)
- [Install with the build](doc/install_build.md)
- [Install with docker](doc/install_docker.md)
- [Build an executable with Pyinstaller](doc/build_with_pyinstaller.md)

## Usage
- Get help usage with `-h`, `--help` or `--usage` options, then run:
```bash
silkaj <sub-command>
```

- Will automatically request and post data on `duniter.org 10901` main Ğ1 node.

- Specify a custom node with `-p` option:
```bash
silkaj <sub-command> -p <address>:<port>
```

## Features
### Currency information
- Currency information
- Display the current Proof of Work difficulty level to generate the next block
- Check the current network
- Explore the blockchain block by block

### Money management
- Send transaction
- Consult the wallet balance

### Money management
- Check sent and received certifications and consult the membership status of any given identity in the Web of Trust
- Check the present currency information stand
- Send certification

### Authentication
- Three authentication methods: Scrypt, file, and (E)WIF

## Wrappers
- [Install as a drop-down for GNOME Shell with Argos](doc/argos.md)
- [How-to: automate transactions and multi-output](doc/how-to_automate_transactions_and_multi-output.md)
- [Transaction generator written in Shell](https://gitlab.com/jytou/tgen)

### Dependencies
Silkaj is based on Python dependencies:

- [Tabulate](https://bitbucket.org/astanin/python-tabulate/overview): to display charts.
- [Commandlines](https://github.com/chrissimpkins/commandlines): to parse command and sub-commands.
- [PyNaCl](https://github.com/pyca/pynacl/): Cryptography (NaCl) library.
- [scrypt](https://bitbucket.org/mhallin/py-scrypt): scrypt key derivation function.
- [pyaes](https://github.com/ricmoo/pyaes): Pure-Python implementation of AES

### Names
I wanted to call that program:
- bamiyan
- margouillat
- lsociety
- cashmere

I finally called it `Silkaj` as `Silk` in esperanto.

### Website
- [Silkaj website sources](https://git.duniter.org/websites/silkaj_website/)
