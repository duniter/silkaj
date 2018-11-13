# How-to: automate transactions and multi-output  

Once silkaj installed. We want to be able to send a transaction to many recipients and to automate that process.

Tutoriel based on this [forum post (fr)](https://forum.duniter.org/t/silkaj-installation-virements-automatiques-et-multi-destinataires/4836).

### Create a recipient file
You have to create a list of the public keys addresses to the recipients you wants to send money.

> Example: here, we want to send money to Duniter’s pubkeys contributors.

Create a `recipients.txt` file containing the list of the recipients keys. You can gather them with `silkaj id <user_id>`.

> Example: 
>
>```txt
>2ny7YAdmzReQxAayyJZsyVYwYhVyax2thKcGknmQy5nQ
>FEkbc4BfJukSWnCU6Hed6dgwwTuPFTVdgz5LpL4iHr9J
>D9D2zaJoWYWveii1JRYLVK3J4Z7ZH3QczoKrnQeiM6mx
>HbTqJ1Ts3RhJ8Rx4XkNyh1oSKmoZL1kY5U7t9mKTSjAB
>38MEAZN68Pz1DTvT3tqgxx4yQP6snJCQhPqEFxbDk4aE
>5cnvo5bmR8QbtyNVnkDXWq6n5My6oNLd1o6auJApGCsv
>GfKERHnJTYzKhKUma5h1uWhetbA8yHKymhVH2raf2aCP
>7F6oyFQywURCACWZZGtG97Girh9EL1kg2WBwftEZxDoJ
>CRBxCJrTA6tmHsgt9cQh9SHcCc8w8q95YTp38CPHx2Uk
>2sZF6j2PkxBDNAqUde7Dgo5x3crkerZpQ4rBqqJGn8QT
>4FgeWzpWDQ2Vp38wJa2PfShLLKXyFGRLwAHA44koEhQj
>55oM6F9ZE2MGi642GGjhCzHhdDdWwU6KchTjPzW7g3bp
>BH8ZqCsp4sbHeDPPHpto53ukLLA4oMy4fXC5JpLZtB2f
>```

### Create an authentication file
To process automated transactions, Silkaj needs to have an authentication file allowing to spent money.

In order to create this file, with your wallet’s secret credentials, run following command:

```bash
silkaj generate_auth_file
Please enter your Scrypt Salt (Secret identifier): 
Please enter your Scrypt password (masked): 
Using default values. Scrypt parameters not specified or wrong format
Scrypt parameters used: N: 4096, r: 16, p: 1
Authentication file 'authfile' generated and stored in current folder for following public key: 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Run the transaction
Finally, you just have to run following command:

```bash
silkaj tx --auth-file --amountUD 20 --output `cat recipients.txt | tr '\n' ':' | sed -e 's/:*$//'`
```

Note: Each pubkey will receive 20 UD.

### Automated transaction
If you want to automate a transaction on each first day of the month, you can set a `crontab` on your machine (preferably a server running 7/24):

```bash
0 0 1 * * silkaj tx --auth-file --yes --amountUD 20 --output `cat recipients.txt | tr '\n' ':' | sed -e 's/:*$//'`
```

Note: the `--yes` option won’t prompt a confirmation.
