## Install Silkaj in a development environement with Poetry

### Install libsodium

```bash
sudo apt install libsodium23 # Debian Buster
sudo apt install libsodium18 # Debian Stretch
sudo dnf install libsodium # Fedora
```

### Install Poetry
- [Installation documentation](https://poetry.eustace.io/docs/#installation)

### On Debian Buster
```bash
sudo apt install python3-pip python3-venv
pip3 install poetry --user --pre
```

### Install dependencies and the Python environment
```bash
git clone https://git.duniter.org/clients/python/silkaj
cd silkaj
poetry install
```

### Run Silkaj
Within `silkaj` repository, enter the development environement and run Silkaj:
```bash
poetry shell
./bin/silkaj
```

You might need to enter Poetry shell to access development tools such as `pytest` or `black`.

### Make Silkaj accessible from everywhere

Add following alias to your shell configuration:
```bash
alias silkaj="cd /path/to/silkaj/silkaj && poetry run -- silkaj"
```
