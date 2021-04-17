## v0.9.0 (17th April 2021)

### [Milestone v0.9.0](https://git.duniter.org/clients/python/silkaj/milestones/13)

- #345, #385, !171: Refactor `id`/`lookup` command exclusively using `/wot/lookup`
  - Display non-member uids when passing a pubkey
  - Use same algorithm as `choose_identity()` uses
  - Rename `id` to `lookup` command
- #377, !172: `balance`: Fix undefined variable in case of 'Total' label

Plus what can be found bellow in v0.9.0rc


## v0.9.0rc (24th March 2021)
### Code
#### `tx`
- #281, !129: Handle transaction size limit properly
- #257, #312, #356: Handle chained transactions/Change txs lost while sending big amount
- #296, #362, !154, !157: Prevent sending transaction with 0 as amounts
- #172, !165: Refactor tx confirmation, by using `click.confirm()`

#### `balance`
- #300, !164: `balance`: Display corresponding member identity uid
- #366, !159: Fix wrong `DuniterError` exception handling in `wot.identity_of`
- #377, !166: `balance`: Document `money.show_amount_from_pubkey()`
- #342, !151: Don’t allow to pass multiple times the same pubkey to the `balance` command

#### Others
- #218, !160: `history`: Add option to display the complete pubkeys
- #314, !165: Display option for `cert`, `membership` commands
- !165: Make `--dry-run` option a generic one
- #378, !165: Create and use generic `send_doc_confirmation()` in `cert` and `membership` commands
- #176, !149: Get rid of `PyNaCl` and use `base58` module
- #309, !163: `wot`: Fix legend about received certifications
- #208: `argos`: Remove duplicate call to `CurrencySymbol`

#### Tests
- #213, !130: Write unit tests for the `tx` command
- #282, !130: Split `patched.py` into files
- #335, !130: Merge the two functions testing `transaction_amount()`
- #363, !129: Returns balance from `patched_get_source()`
- #368, !161: Assertions are not tested when testing system exit
- #362, !156: Change "moul" id in tests

### Meta
- #240, !150: Drop Python 3.5 support
- #294, !150, docker/python3/poetry!1: Add support and set-up Python 3.9 test job
- #270: Silkaj v0.8.1 package for Debian Bullseye (v11)
- #226, !158: Get rid of `ipaddress` dependency
- #290, !162: Update `pre-commit` dev dependency
- #267: Update the copyright date to 2021 in the headers of every source files
- !150, !155, !167, Update DuniterPy from v0.58.1 to v0.62.0
- #313, !148: Be compatible with and handle new features from Poetry v1.1
- #299, !147: Introduce dev version suffix

---
Thanks @matograine, @moul, @atrax

## v0.8.1 (30th November 2020)
- #358, !152: Update DuniterPy to v0.58.1, to support `libnacl` v1.7.2

Thanks @matograine

## v0.8.0 (18th October 2020)

### [Milestone v0.8.0](https://git.duniter.org/clients/python/silkaj/milestones/8)

### Code
#### Transaction
- #111, !108: Support passing different amounts on multi-recipients tx
  - **Breaking change**: Rename `--output` option to `--recipient`
- Add extra small options to ease passing multiple amounts and recipients:
  - `-a/--amount`
  - `-d/--amountUD`
  - `-r/--recipient`
  - `-c/--comment`
- Add possibility to pass multiple options:
  - **Breaking change**: recipients public keys are no longer `:` separated: `-r A -r B`

- #232, !131, !132: Identities not retrieved for tx with several issuers, and to display the tx history
- #236, !107: Improve the confirmation display
- !144: Rework confirmation fields titles
- #235: Make sure only one option is passed to retrieve the amount of the transaction

#### Membership, WoT
- #88, !140: Add `membership` command
- #88, !144: Rework table fields names
- #140, !140: Ability to pass an `uid` or a `pubkey` to `wot`, and `cert`, `membership` commands
  - Implement identity choice selector

#### Checksum
- #237, !132: **Breaking change**: Switch back the checksum delimiter from `!` to `:`
- #323, !132: Handle pubkey's checksum in the tx code
- #301, !143: Generalize pubkey checksum display and verifiction, Add `chekcsum` command
- #320, !143: Incorrect use of `check_public_key()` in `id` command

#### Others
- #262, !123: Add new `verify` command to check blocks’ signatures
- #264, !133: Disable the broken `net` command
- !131: Display `powMin` in a row in the `blocks` explorer
- #210, !115: Close client session in every cases
- #223: Make Click context optional to be able to call functions from an external module
- #255, !113: `balance`: display the content in tables
- #269, !133: Move `convert_time()` to `tui.py`
- #278, !128: Fix PubSec regex
- #336, !141: `history`: Pubkeys display issue with multisig txs

### Dev Env
#### Poetry migration
- #182: Migrate from Pipenv and `setup.py` to Poetry
- #249: Install Poetry stable when v1 is released
- #263, !127: Post migration tasks (black, poetry)
- #276, !120: Pip installation do not install `silkaj` executalbe into `$HOME/.local/bin`

#### CI/CD set-up
- #245: Automated containers builds with Poetry installed for Python versions 3.5, 3.6, 3.7, and 3.8
- #149: CI/CD set up
- #105: Deploy on PyPI from GitLab CD
- #146: Add a coverage badge
- #284, !124: `build` and `tests` jobs are not retriggered in case of source code change
- #286, !126: Use latest Black version from PyPI in the container
- !131: Use `rules` instead of `only/except`

#### Tests
- #241: Can not run test with Click utility

### Dependencies
- #259: `attr` error while installing with `pip`
- !121, !131, !142: Update DuniterPy from v0.55.1 to v0.58.0
- #251, !140: Introduce `pendulum` date utility
- Introduce `pytest-sugar`
- Update PyNaCl to v1.4.0
- Update Click to v7.1.2
- #338, !140: Update black to v20

### Python versions support
We added the support for Python 3.8.
#240: It is planned that v0.8.x versions are going to be the last releases with Python 3.5 support
since [its support from the Python project has been dropped September 30th of 2020](https://pythoninsider.blogspot.com/2020/10/python-35-is-no-longer-supported.html).

### Documentation
- #202: Document contribution process in `CONTRIBUTING.md`
- #182: Document Poetry installation and usage
- !109: Add Poetry installation on Debian Buster 
- !103: Add pip installation documentation for macOS
- !131: Add packaging status badge from Repology
- #244: Add `AUTHORS.md` listing the contributors
- #207: Create Silkaj SVG logo

### Project
- #252, !118: Create a script to update and update the copyright date to 2020
- #285, !132: Add copyright and license statements in tests source files

### Thanks
@moul, @matograine

---

## v0.7.6 (24th January 2020)
- Update DuniterPy to v0.55.1 in order to have the PubSec regex fixed

## v0.7.5 (23th January 2020)
- #276: Publish on PyPI with previous method: `wheel`, `twine`, and `setup.py`.
- `silkaj` binary does not get installed to `$HOME/.local/bin` via Poetry

## v0.7.4 (22th January 2020)
- #273, !119: Fix broken PubSec authfile importation regex

Thanks to @matograine for this bugfix and the release!

## v0.7.3 (25th July 2019)
#239: Bug fix release for broken successives transactions due to wrongly calculated pending inputs:
- remove already used inputs: restore previous behaviour which haven’t been kept the same during the migration
- `enumerate()` wrongly moved to the non appropriate for loop

## v0.7.2 (25th June 2019)
- #233: fix round passed amount and amoundUD floats × by 100

## v0.7.1 (29th May 2019)
- Fix transaction document generation from DuniterPy

## v0.7.0 (22th May 2019)
### [Milestone v0.7.0](https://git.duniter.org/clients/python/silkaj/milestones/10)

#### DuniterPy
- #7, !97: Migrate to DuniterPy
- #200: Freeze DuniterPy dependency version
- #206: Set a sleep for async requests
- #178: Select different sources for intermediaries tx

#### CLI
- #77, !98: Migrate command line tool from commandline to Click
- #67, #76, #116, #117, #123: fixed by previous issue
- #167: Rename `amount` command to `balance`
- #148: Rename `issuers` command to `blocks` which is a more appropriate word to what it does
- With `-p` option: when the port of the node is 443, it’s not necessary to specify the port

#### Transaction
- #22: Display transactions history in a table 
- #184: Rework transaction functions (Part 3)
- #152: fix `--allSources` option which was not working
- #165, !99: Display outputBackChange option in confirmation chart
- #131: Prevent sending too small amount

#### Certification
- #170: Change process: only propose license display
- #198: Display identity’s blockstamp and date into confirmation message

#### Difficulty level
- #93: Difficulties fails / use websocket to be informed about new block
- #190: Display the date when the head block has been generated

#### Balance
- !96, #122: display balance in comparison to the average of money share

#### Blocks
- Display the full dates of blocks’ generation and mediantime

#### WoT
- #141: Crash on membership status
- Add legend to explain `✔` 
- #189: Handle wot requests exceptions
- #135 :is_member() requests all members to know if an identity is member will explose

#### Authentication
- #130: Prevent erasing authfile
- Use `pathlib.Path` instead of `os.path`

#### Tests
- !83, #85: Create test structure
- #225: Install `pytest-asyncio`

#### Other
- #161: Singleton improvement
- #157, !100: Use `for` loops
- #169, !100: type issue
- #113: Many small improvements

#### Website / Doc
- #82: Update website and readme about new features
- #136: Link directly the installation documentation on the website
- #159: Update website
- #160: Add website repository link in the README
- List Silkaj wrappers en the README

##### Installation documentation
- Add instructions on installing libsodium which is required by pylibscrypt since DuniterPy migration
- #142: Improve pip installation documentation
- Improve Pipenv installation documentation
- !89: Add Docker install procedure, Pip: dependency and PATH tricks
- #215: Conflict between pyproject.toml and pipenv install

#### Windows
- #153: Install on Windows, Scrypt issue
- #154: net: can’t get screen size on Windows
- !92:  Document Windows installation with pip

#### Project
- #132: Add a license notice as a header of every source files
- #158: Add CHANGELOG.md file
- #186: Fix firsts two tags
- Pypi: add classifiers

#### Thanks
@Attilax, @Bernard, @cebash, @matograine, @vtexier

## v0.6.5 Debian (8th January 2019)

v0.6.5 fork for Debian package without DuniterPy migration but with Click CLI module.

- #137: Create Debian package and publish it in Buster
- #77, !98: Migrate to Click
- #132: Add a license notice as a header of every source files

#### Thanks
@jonas

## v0.6.1 (10th December 2018)

### [Milestone v0.6.1](https://git.duniter.org/clients/python/silkaj/milestones/11)

- !90, #151: Fix intermediaries transactions sent to wrong recipient
- !91, #145: Allow to renew certifications
- #155: Make `clear` calls works on Windows
- #141: Crash on membership status
- #166: Shell completion


## v0.6.0 (18th November 2018)

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

## v0.5.0 (22th May 2018)

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


## v0.4.0 (28th January 2018)
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


## v0.3.0 (17th April 2017)
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

## v0.2.0 (27th March 2017)
### Features
- [Transaction feature](https://github.com/duniter/silkaj/pull/21)
- [Output information on the drop-down menu with Argos (GNOME Shell extension)](https://github.com/duniter/silkaj/pull/20)

### [Milestone v0.2.0](https://git.duniter.org/clients/python/silkaj/milestones/4)

### Announcement
- [Diaspora* post](https://framasphere.org/posts/3055642)

Big thanks to @Tortue95, and @mmuman.

## v0.1.0 (23th September 2016)

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
