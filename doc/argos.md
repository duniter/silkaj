## Install as a drop-down for GNOME Shell with Argos
Under GNOME Shell, with [Argos](https://github.com/p-e-w/argos) extension:

- [Install Argos](https://github.com/p-e-w/argos#installation)
- Inside `~/.config/argos/silkaj.30s.sh` put:

```bash
#!/usr/bin/env bash
/path/to/silkaj/silkaj argos
```

Add execution permission:
```bash
chmod u+x ~/.config/argos/silkaj.30s.sh
```

Argos will run the script every 30 seconds.
