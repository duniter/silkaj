# Install Silkaj with Pipenv

### Install libsodium

```bash
sudo apt install libsodium23 # Debian Buster
sudo apt install libsodium18 # Debian Stretch
sudo dnf install libsodium # Fedora
```

### Install pipenv

- [Pipenv installation instructions](https://github.com/pypa/pipenv#installation)

### Retrieve silkaj sources
```bash
git clone https://git.duniter.org/clients/python/silkaj.git
cd silkaj
```

### Install with dependencies
```bash
pipenv install "-e ."
```

The double quotes are important, if you forget them, `pipenv` will install silkaj from pypi

### Activate pipenv and run silkaj
```bash
pipenv shell
silkaj
```

## Manage Python versions with Pyenv

If you have trouble with the pipenv install, may be the Python version installed on your system is not up to date.
To install and manage easily multiple Python version, use Pyenv:

### Install pyenv on your home
```bash
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
```

Add in `~/.bash_profile`, in `~/.bashrc` on Fedora or Ubuntu:

```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv virtualenv-init -)"
eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
```

Reload your bash config:

    source ~/.bashrc

or

    source ~/.bash_profile

### Install Python version required

    pyenv install 3.7.2

### Select Python version for the current shell

    pyenv shell 3.7.2

Pipenv will search the `Pyenv` Python version chosen before the system version.
