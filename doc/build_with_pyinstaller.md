# Build with Pyinstaller

## Install Pyinstaller
```bash
pip install pyinstaller
```

If you are using Pyenv, don’t forget to save pyinstaller install:
```bash
pyenv rehash
```

## Build
```bash
pyinstaller src/silkaj.py --hidden-import=_cffi_backend --hidden-import=_scrypt --onefile
```

You will found the exetuable file on `silkaj/dist` folder.
