# Install Silkaj with Pip

## Install dependencies

```bash
sudo apt install python3-pip libssl-dev
```

On Ubuntu (14.04 and 16.04) and Debian 8, you need this package too:
```bash
sudo apt install libffi-dev
```

Your system must use UTF-8 locales.

Linux Mint is reported to require the installation of this package too:
```
sudo apt install python3-dev
```

## Install from Pypi

```bash
pip3 install silkaj --user
```

After intallation, if you get a `bash: silkaj: command not found` error, you should add `~/.local/bin` to your `PATH`:
```bash
echo "export PATH=$PATH:$HOME/.local/bin" >> $HOME/.bashrc
source $HOME/.bashrc
```

## Install from sources

### Retrieve silkaj sources
```bash
sudo apt install git
git clone https://git.duniter.org/clients/python/silkaj.git
cd silkaj
```

### Install with dependencies

Just install:
```bash
pip3 install .
```

Or install it as "editable", for development:
```bash
pip3 install -e .
```

