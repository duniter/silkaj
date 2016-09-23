# Silkaj

CLI Duniter client written with Python 3.

## Dependencies
```bash
sudo pip3 install requirements.txt
```

## Usage
- Get help usage with `-h`, `--help` or `--usage` options, then run:
```bash
./src/silkaj.py <subcommand>
```

- Will automatically request `duniter.org 8999` node.

- Specify a custom node with `--peer` or `-p` option:
```bash
./src/silkaj.py <subcommand> --peer <address>:<port>
```

## Features
- Currency information
- Proof-of-Work difficulties
- network information tab:
 - endpoints, ip6, ip4, domain name and port. Handle nodes sharing same pubkey.
 - pubkey, uid, if member.
 - Proof-of-Work difficulties.
 - generated block and median times.
 - nodes versions.
 - current block n°, hash and time.
- Issuers last ones or all

### Names
I wanted to call that program:
- bamiyan
- margouillat
- lsociety
- cashmere
