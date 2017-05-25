# Install Silkaj on a Python environment

## Install Pyenv

### Install pyenv tools
```bash
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
```

### Handle shell modifications: point 2,3 and 4.
- [Follow pyenv install documentation](https://github.com/pyenv/pyenv#installation)


### Install latest Python version and create pyenv
```bash
pyenv install 3.6.0
pyenv shell 3.6.0
pyenv virtualenv silkaj-env
```

## Install Silkaj

### Retrieve silkaj sources
```bash
git clone https://github.com/duniter/silkaj.git
cd silkaj
```

### Install dependencies and store them on pyenv environement
```bash
pip install -r requirements.txt --upgrade
pyenv rehash
```

### Activate pyenv and run silkaj
```bash
pyenv activate silkaj-env
./silkaj
```
