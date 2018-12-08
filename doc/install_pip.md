# Install Silkaj with Pip

Have to use a shell in linux or a command tool (cmd.exe) on windows.

Assuming that python and pip version 3 are installed and available. You can check with
```bash
pip3 --version
```

## Install directly from internet (implicitely uses binaries from website Pypi)

### installing for all users

```bash
pip3 install silkaj
```

### installing for current user only

```bash
pip3 install silkaj --user
```

### upgrading

```bash
pip3 install silkaj --user --upgrade
```

### uninstalling (useful to see the real pathes)

```bash
pip3 install silkaj --user
```

### testing silkaj

```bash
silkaj info
```

## On linux 

### Your system must use UTF-8 locales...

### Install dependencies before installing

```bash
sudo apt install python3-pip libssl-dev
```

On Ubuntu (14.04 and 16.04) and Debian 8, you need this package too:
```bash
sudo apt install libffi-dev
```

Linux Mint is reported to require the installation of this package too:
```
sudo apt install python3-dev
```

### Completing PATH

After intallation, if you get a `bash: silkaj: command not found` error, you should add `~/.local/bin` to your `PATH`:
```bash
echo "export PATH=$PATH:$HOME/.local/bin" >> $HOME/.bashrc
source $HOME/.bashrc
```

## On windows

### administrator rights
Please note administrator rights may be mandatory for some of these operations.

### PATH variable

The main problem on Windows is about finding where are the requested files.

Python must be installed (version 3 minimum). For instance https://sourceforge.net/projects/winpython/

You can test that python is available by opening a command tool (cmd.exe) and trying:
```bash
C:\>python --version
Python 3.6.7

C:\>
```

When installing Python, be careful which folder you specify (for instance C:\WPy-3670)

After install you commonlly have to add yourself this folder in the PATH environment variable:

To make it by command tool (cmd.exe) :
```bash
set PATH=%PATH%;C:\WPy-3670\
```
then you have to exit the cmd tool so that PATH variable be upgraded internally.

You may also use RightClick on computer, then Advanced System Parameters and use in the bottom the button Environment Variables.

In order to be able to use silkaj and specifically the OpenSSL binaries, you also have to add the following folder to the PATH variable:
C:\WPy-3670\python-3.6.7.amd64\Lib\site-packages\PyQt5\Qt\bin\

```bash
set PATH=%PATH%;C:\WPy-3670\python-3.6.7.amd64\Lib\site-packages\PyQt5\Qt\bin\
```

If not, you will obtain this error while testing silkaj:
```bash
C:\WPy-3670\python-3.6.7.amd64\Scripts>silkaj info
Traceback (most recent call last):
File "C:\WPy-3670\python-3.6.7.amd64\Scripts\silkaj", line 7, in <module>
from silkaj.cli_tools import manage_cmd
File "C:\WPy-3670\python-3.6.7.amd64\lib\site-packages\silkaj\cli_tools.py", line 5, in <module>
from silkaj.tx import send_transaction
File "C:\WPy-3670\python-3.6.7.amd64\lib\site-packages\silkaj\tx.py", line 14, in <module>
from silkaj.auth import auth_method
File "C:\WPy-3670\python-3.6.7.amd64\lib\site-packages\silkaj\auth.py", line 5, in <module>
from scrypt import hash
File "C:\WPy-3670\python-3.6.7.amd64\lib\site-packages\scrypt\__init__.py", line 1, in <module>
from .scrypt import *
File "C:\WPy-3670\python-3.6.7.amd64\lib\site-packages\scrypt\scrypt.py", line 15, in <module>
_scrypt = cdll.LoadLibrary(imp.find_module('_scrypt')[1])
File "C:\WPy-3670\python-3.6.7.amd64\lib\ctypes\__init__.py", line 426, in LoadLibrary
return self._dlltype(name)
File "C:\WPy-3670\python-3.6.7.amd64\lib\ctypes\__init__.py", line 348, in init
self._handle = _dlopen(self._name, mode)
OSError: [WinError 126] Le module spécifié est introuvable

C:\WPy-3670\python-3.6.7.amd64\Scripts>
```

### creating the silkaj command file silka.bat

In order to be able to launch silkaj as a windows command, you have to create a file silkaj.bat in the following folder:
C:\WPy-3670\python-3.6.7.amd64\Scripts\silkaj.bat

containing exactly:
rem @echo off
python "%~dpn0" %*

and then to add this folder in the PATH variable :
```bash
set PATH=%PATH%;C:\WPy-3670\python-3.6.7.amd64\Scripts\
```



---

## Install from original sources in duniter website

### Retrieve silkaj sources on linux
```bash
sudo apt install git
git clone https://git.duniter.org/clients/python/silkaj.git
cd silkaj
```

### Retrieve silkaj sources on windows

You have first to install the git tool from https://git-scm.com/download/win

Then change directory to where you want to download the sources, for instance:
```bash
cd  ~/appdata/Roaming/
```

Then download the silkaj source (dev version) with git tool
which will create a folder silkaj

```bash
 git clone https://git.duniter.org/clients/python/silkaj.git
 ```
 
Then change directory to the downloaded folder
```bash
 cd ~/appdata/Roaming/silkaj
```

### then Install with dependencies

Just install
after being sure you have changed directory to the downloaded folder
```bash
pip3 install .
```

Or install it as "editable", for development:
```bash
pip3 install -e .
```

