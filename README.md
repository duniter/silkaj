# Silkaj
[![Version](https://img.shields.io/pypi/v/silkaj.svg)](https://pypi.python.org/pypi/silkaj) [![License](https://img.shields.io/pypi/l/silkaj.svg)](https://pypi.python.org/pypi/silkaj) [![Python versions](https://img.shields.io/pypi/pyversions/silkaj.svg)](https://pypi.python.org/pypi/silkaj)

- CLI Duniter client written with Python 3.
- [Website](https://silkaj.duniter.org)

## Install
```bash
pip3 install silkaj --user
```

- [Install with Pip](doc/install_pip.md)
- [Install the Development environment](doc/install_poetry.md)
- [Install with the build](doc/install_build.md)
- [Build an executable with Pyinstaller](doc/build_with_pyinstaller.md)

## Usage
- Get help usage with `-h` or `--help` options, then run:
```bash
silkaj <sub-command>
```

- Will automatically request and post data on `duniter.org 443` main Ğ1 node.

- Specify a custom node with `-p` option:
```bash
silkaj -p <address>:<port> <sub-command>
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

### Web-of-Trust management
- Check sent and received certifications and consult the membership status of any given identity in the Web of Trust
- Check the present currency information stand
- Send certification

### Authentication
- Three authentication methods: Scrypt, file, and (E)WIF

## Wrappers
- [Install as a drop-down for GNOME Shell with Argos](doc/argos.md)
- [How-to: automate transactions and multi-output](doc/how-to_automate_transactions_and_multi-output.md)
- [Transaction generator written in Shell](https://gitlab.com/jytou/tgen)
- [Ğ1Cotis](https://git.duniter.org/matograine/g1-cotis)
- [G1pourboire](https://git.duniter.org/matograine/g1pourboire)
- [Ğ1SMS](https://git.duniter.org/clients/G1SMS/)
- [Ğmixer](https://git.duniter.org/tuxmain/gmixer-py/)

### Dependencies
Silkaj is based on Python dependencies:

- [Click](https://click.palletsprojects.com/): Command Line Interface Creation Kit.
- [DuniterPy](https://git.duniter.org/clients/python/duniterpy/): Python APIs library to implement duniter clients softwares.
- [Tabulate](https://bitbucket.org/astanin/python-tabulate/overview): to display charts.

### Names
I wanted to call that program:
- bamiyan
- margouillat
- lsociety
- cashmere

I finally called it `Silkaj` as `Silk` in esperanto.

### Website
- [Silkaj website sources](https://git.duniter.org/websites/silkaj_website/)

## Packaging status
[![Packaging status](https://repology.org/badge/vertical-allrepos/silkaj.svg)](https://repology.org/project/silkaj/versions)
