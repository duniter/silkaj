# Install Silkaj with Pip

You have to use a shell on GNU/Linux or a command tool (`cmd.exe`) on Windows.

## GNU/Linux 
The system must use UTF-8 locales…

### Install libsodium

```bash
sudo apt install libsodium23 # Debian Buster
sudo apt install libsodium18 # Debian Stretch
sudo dnf install libsodium # Fedora
```

### Install dependencies before installing

```bash
sudo apt install python3-pip libssl-dev
```

On Ubuntu (14.04 and 16.04) and Debian 8, you need this package too:
```bash
sudo apt install libffi-dev
```

Linux Mint is reported to require the installation of this package too:
```bash
sudo apt install python3-dev
```

### Completing `PATH`

After intallation, if you get a `bash: silkaj: command not found` error, you should add `~/.local/bin` to your `PATH`:
```bash
echo "export PATH=$PATH:$HOME/.local/bin" >> $HOME/.bashrc
source $HOME/.bashrc
```

## Windows

### Administrator rights
Please note that the administrator rights might be mandatory for some of these operations.

### The `PATH` variable

The main issue on Windows is about finding where are the requested files.

Python must be installed (version 3.5 minimum). For instance https://sourceforge.net/projects/winpython/

You can test that Python is available by opening a command tool (cmd.exe) and running:
```bash
C:\>python --version
Python 3.6.7
```

When installing Python, take care to specify the good folder (for instance: `C:\WPy-3670`)

After the installation, you commonly have to add by yourself this folder in the `PATH` environment variable:

To make it by command tool (cmd.exe):
```bash
set PATH=%PATH%;C:\WPy-3670\
```
Then you have to exit the cmd tool so that `PATH` variable can be updated internally.

You may right click on computer, then go to Advanced System Parameters and use in the bottom the button Environment Variables.

In order to be able to use silkaj and specifically the OpenSSL binaries, you also have to add the following folder to the `PATH` variable:
C:\WPy-3670\python-3.6.7.amd64\Lib\site-packages\PyQt5\Qt\bin\

```bash
set PATH=%PATH%;C:\WPy-3670\python-3.6.7.amd64\Lib\site-packages\PyQt5\Qt\bin\
```

### Creating the command file `silkaj.bat`

In order to be able to launch silkaj as a Windows command, you have to create a file `silkaj.bat` in the following folder:
`C:\WPy-3670\python-3.6.7.amd64\Scripts\silkaj.bat`

containing:
```bash
rem @echo off
python "%~dpn0" %*
```

and then to add this folder into the `PATH` variable:
```bash
set PATH=%PATH%;C:\WPy-3670\python-3.6.7.amd64\Scripts\
```

## Install directly from internet (implicitely uses binaries from website Pypi)

Assuming that Python v3 and pip version 3 are installed and available. You can check with:
```bash
pip3 --version
```

### Install for all users

```bash
pip3 install silkaj
```

### Install for current user only

```bash
pip3 install silkaj --user
```

### Upgrade

```bash
pip3 install silkaj --user --upgrade
```

### Uninstall (useful to see the real paths)

```bash
pip3 uninstall silkaj --user
```

### Check silkaj is working

```bash
silkaj info
```

---

## Install from original sources from the forge

### Retrieve silkaj sources on linux
```bash
sudo apt install git
git clone https://git.duniter.org/clients/python/silkaj.git
cd silkaj
```

### Retrieve silkaj sources on Windows

First, you have to install the git tool from https://git-scm.com/download/win

Then change directory to where you want to download the sources, for instance:
```bash
cd  ~/appdata/Roaming/
```

Then download Silkaj sources (`dev` branch) with git tool
which will create a folder silkaj

```bash
 git clone https://git.duniter.org/clients/python/silkaj.git
```

Then change directory to the downloaded folder
```bash
 cd ~/appdata/Roaming/silkaj
```

### Install

After being sure you have changed directory to the downloaded folder
```bash
pip3 install .
```

Or install it as "editable", for development:
```bash
pip3 install -e .
```
