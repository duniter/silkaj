"""
Copyright  2016-2019 Maël Azimi <m.a@moul.re>

Silkaj is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Silkaj is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Silkaj. If not, see <https://www.gnu.org/licenses/>.
"""

import webbrowser
from pydoc import pager
from sys import exit
from click import command


def license_approval(currency):
    if currency != "g1":
        return
    display_license()
    if input("Do you approve Ğ1 license [yes/no]? ") != "yes":
        exit(1)


@command("license", help="Display Ğ1 license")
def license_command():
    display_license()


def display_license():
    language = input("In which language would you like to display Ğ1 license [en/fr]? ")
    if language == "en":
        if not webbrowser.open("https://duniter.org/en/wiki/g1-license/"):
            pager(open("licence-G1/license/license_g1-en.rst").read())
    else:
        if not webbrowser.open("https://duniter.org/fr/wiki/licence-g1/"):
            pager(open("licence-G1/license/license_g1-fr-FR.rst").read())
