# Install Silkaj on the system

## Retrieve sources
Clone repository:
```bash
git clone https://github.com/duniter/silkaj.git
```

## Dependencies
You may install dependencies.
You could install all dependencies from `pip`.
If you choose to install from distribution packages, some dependencies could be missing.
You will have to install them with `pip`.

### From pip
```bash
sudo pip3 install -r requirements.txt
```
Use `pip` command if `pip3` is not present.
Upgrade `pip` adding `--upgrade pip` to previous command.

### From distributions package managers
#### Debian-like
```bash
sudo apt-get install python-tabulate python-ipaddress
```

#### Fedora
```bash
sudo dnf install python-devel python-ipaddress python3-tabulate python3-pynacl python3-devel python-pyaes
```
