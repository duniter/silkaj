"""
Copyright  2016-2021 Maël Azimi <m.a@moul.re>

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
from click import command, echo_via_pager, confirm


def license_approval(currency):
    if currency != "g1":
        return
    if confirm(
        "You will be asked to approve Ğ1 license. Would you like to display it?"
    ):
        display_license()
    confirm("Do you approve Ğ1 license?", abort=True)


@command("license", help="Display Ğ1 license")
def license_command():
    display_license()


def display_license():
    language = input("In which language would you like to display Ğ1 license [en/fr]? ")
    if language == "en":
        if not webbrowser.open("https://duniter.org/en/wiki/g1-license/"):
            echo_via_pager(open("licence-G1/license/license_g1-en.rst").read())
    else:
        if not webbrowser.open("https://duniter.org/fr/wiki/licence-g1/"):
            echo_via_pager(open("licence-G1/license/license_g1-fr-FR.rst").read())
