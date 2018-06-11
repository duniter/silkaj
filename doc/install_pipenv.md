# Install Silkaj with Pipenv

### Install pipenv

- [Pipenv installation instructions](https://github.com/pypa/pipenv#installation)

### Retrieve silkaj sources
```bash
git clone https://git.duniter.org/clients/python/silkaj.git
cd silkaj
```

### Install dependencies
```bash
pipenv install
```

### Activate pipenv and run silkaj
```bash
pipenv shell
./silkaj
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

    pyenv install 3.6.0

### Select Python version for the current shell

    pyenv shell 3.6.0

Pipenv will search the `Pyenv` Python version chosen before the system version.
