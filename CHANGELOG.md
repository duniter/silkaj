## v0.6.1 (10 December 2018)

- !90, #151: Fix intermediaries transactions sent to wrong recipient
- !91, #145: Allow to renew certifications
- #155: Remove clear calls which are not availabre on non-Unix

## v0.6.0 (18 November 2018)

### [Milestone v0.6.0](https://git.duniter.org/clients/python/silkaj/milestones/7)

#### Installation
- #86: Move from `pyenv+pip` to Pipenv as the new development environment solution
- #100, !80: New installation method with `pip` now set as default
- #100: Documentation on how to publish on Pypi

#### Authentication
- #78: Use Scrypt as default authentication method
- #102: Display a confirmation message after using `generate_auth_file` command
- #103: More explicit usage about the authentication file mechanism storage

#### Certification
- #96, !82: Certification fails for non-members identities
- Prevent certifying ourself
- Code refactoring: simplification, duplicate code removal

#### Wot
- Display certification stock
- #73: Display identity status:
  - Display membership expiration due to membership expiration and certifications expiration
- #127: fix: display human readable date for 'revoked on' attribute

#### Transaction
- #83, !78: Allow multi-output transactions
- #72: Check the pubkey’s balance is enough before processing the transaction
- #72: Minors transaction refactoring
- #101: Round UD value in the confirmation summary
- #118: Use generic function to get sources
- #120: Display pubkey’s balance before and after transaction in the confirmation summary
- #125: Fix wrong amount transferred

#### New commands
- #91: `about`: displays information about silkaj
- #95: `license`: displays Ğ1’s license

#### Ğ1-test
- #87: Add `--gtest` option to specify official Ğ1-test node
- #109, !84: Improve gtest usage message
- #112: Amount: fix authentication option with `--gtest` option

#### Python 3.7
- #98: Test with Python 3.7: silkaj is compatible with Python from version 3.4 to 3.7
- #98: Set Python 3.7 for Pipenv

#### Network performances
- #42, !85: Thanks to singleton, requests are made once for `head_block`, blockchain parameters, endpoint, `ud_value`, and `currency_symbol` retrieval
- #32: request the domain first instead of the IP (to handle https certificates) (this avoid `network` view to crash)
- #32, !79: Add timeouts on GET and POST requests
- #128, !88: Fix POST request timeout

#### Black: code formatting
- #94, !76: move from `pep8` to `black` code formatting. Set pre-commit hook and CI worker

#### Bug fixes and refactoring
- #121: Move cryptographic related functions into `crypto_tools.py`

#### Logo
- #92: Silkaj logo publication under GNU APGLv3 after a successful crowdfunding

#### Wrappers
- #107: Document silkaj wrappers usages

### [Forum post](https://forum.duniter.org/t/silkaj-v0-6-0-release/4858)

## v0.5.0 (22 May 2018)

### [Milestone v0.5.0](https://git.duniter.org/clients/python/silkaj/milestones/2)

#### Certification
- #61: sending certification document:
  - check that current identity is member
  - check that the certification has not already been sent
  - prompt Ğ1’s license and ask for acceptance in web browser or in pager (a `less`-like) if no web browser is available 

#### Wot
- #84: display certifications’ expiration date
- #81: bugfix, nothing displayed when there is two identities with same id

#### Amount
- remove necessity to prepend with `--pubkey` option: `silkaj amount pubkey1:pubkey2:pubkey3`

#### Issuers
- display the hash’s ten first characters as Ğ1’s global difficulty has increased
- display blocks in current window: `silkaj issuers 0`

#### Build
- #6: Automate releases using a script

#### Other
- display `Ğ1` and `ĞTest` currencies symbols
- Aliases commands `id`: `identities`, `tx`: `transaction`, `net`: `network`
- `import` rework to improve loading performances
- Lots of code reorganization and cleaning

### [Forum post](https://forum.duniter.org/t/silkaj-v0-5-0/4712)


## v0.4.0 (28 January 2018)
### [Milestone v0.4.0](https://git.duniter.org/clients/python/silkaj/milestones/5)

#### New `wot` command which displays received and sent certification of an identity
- !50, !66 

#### Transaction
- #41: Rework/refactoring of transaction code (part 1)
- !55: Add check condition for sources
- !57: Exit if wrong pubkey’s output formats

#### Amount
- #46, !68: Add ability to display the amount of many pubkey with same command
- Total amount of pubkeys displayed at the end (nice to know how much units you own)

#### Authentication
- !56: Add [Ğannonce](https://gannonce.duniter.org/) (aka PubSec) file format import
- #60: Hide salt at scrypt authentication

#### Difficulties
- !58: Reload/refresh in a loop PoW difficulty level
- Display in same order as [Remuniter](http://remuniter.cgeek.fr/)

#### Id
- #49: Display if pubkey is member
- #59: Bug fix with `id` command

#### Build
- Build published with sha256 checksum

#### Other
- Change default endpoint

#### Thanks
Thanks to @Tortue95, @jytou, @mmuman, and @cuckooland

### [Forum post](https://forum.duniter.org/t/silkaj-0-4-0/4071)


## v0.3.0 (17 April 2017)
### [Milestone v0.3.0](https://git.duniter.org/clients/python/silkaj/milestones/5)

#### Transactions
- enhance transaction command:
  - #27, #30: ask for confirmation
  - !38: new confirmation chart containing transaction informations
  - don’t prompt `scrypt` parameters. See `Auth` §

#### New command `id` to search for pubkey/identity
- !29: new command `id` to search identities with pubkey or id

#### Tutorial to install a Python environment
- #23, !40: Pyenv installation tutorial

#### Authentication
- !45: new authentication method: WIF. For future paper wallet feature
- #39, #43: Don’t prompt scrypt parameters at authentication. Use default ones

#### Builds
- #5: with Pyinstaller

#### Other
- !33, !37: Ability to sort network view
- Change license from GNU GPLv3 to GNU AGPLv3
- !31: Code formatting with `pep8`

Thanks to @Tortue95 and @jytou 

### [Forum post](https://forum.duniter.org/t/lets-send-your-money-silkaj-v0-3-0/2404/1)

## v0.2.0 (27 March 2017)
### Features
- [Transaction feature](https://github.com/duniter/silkaj/pull/21)
- [Output information on the drop-down menu with Argos (GNOME Shell extension)](https://github.com/duniter/silkaj/pull/20)

### [Milestone v0.2.0](https://git.duniter.org/clients/python/silkaj/milestones/4)

### Announcement
- [Diaspora* post](https://framasphere.org/posts/3055642)

Big thanks to @Tortue95, and @mmuman.

## v0.1.0 (23 September 2016)

### Public release
- [Duniter forum post](https://forum.duniter.org/t/silkaj-new-cli-duniter-client/1278)
- [Diaspora* post](https://framasphere.org/posts/2226277)


### [Milestone v0.1.0](https://git.duniter.org/clients/python/silkaj/milestones/1)


### Features
Sub-commands:
- `info`
- `difficulties`
- `network`
- `issuers`


Thanks to @c-geek.
