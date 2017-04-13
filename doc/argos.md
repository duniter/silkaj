## Integrate it on a dropdown menu to the panel
Under GNOME Shell, with [Argos](https://github.com/p-e-w/argos) extension:

- [Install Argos](https://github.com/p-e-w/argos#installation)
- Put inside `~/.config/argos/silkaj.30s.sh`:

```bash
#!/usr/bin/env bash
/path/to/silkaj/silkaj argos
```

Add execution premission:
```bash
chmod u+x ~/.config/argos/silkaj.30s.sh
```

Argos should the script and reload it every 30 seconds.
