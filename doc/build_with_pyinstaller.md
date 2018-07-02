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
pyinstaller bin/silkaj --hidden-import=_cffi_backend --hidden-import=_scrypt --onefile
```

You will found the exetuable file on `dist` folder.
