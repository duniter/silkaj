#!/bin/bash

VERSION=$1

check_argument_specified() {
	if [[ -z $VERSION ]]; then
		error_message "You should specify a version number as argument"
	fi
}

check_version_format() {
	if [[ ! $VERSION =~ ^[0-9]+.[0-9]+.[0-9]+[0-9A-Za-z]*$ ]]; then
		error_message "Wrong format version"
	fi
}

check_branch() {
	branch=`git rev-parse --abbrev-ref HEAD`
	if [[ "$branch" != "master" ]]; then
		error_message "Current branch should be 'master'"
	fi
}

update_version() {
	sed -i "s/SILKAJ_VERSION = \"silkaj.*\"/SILKAJ_VERSION = \"silkaj $VERSION\"/" src/constants.py
	git diff
}

commit_tag() {
	git commit src/constants.py -m "v$VERSION"
	git tag "v$VERSION" -a -m "$VERSION"
}

build() {
	if [[ -z $VIRTUAL_ENV ]]; then
		error_message "Activate silkaj-env"
	fi
	exec_installed pyinstaller
	pyinstaller src/silkaj.py --hidden-import=_cffi_backend --hidden-import=_scrypt --onefile
}

checksum() {
	# Generate sha256 checksum file
	exec_installed sha256sum
	cd dist
	sha256sum silkaj > silkaj_sha256sum
}

exec_installed() {
	if [[ ! `command -v $1` ]]; then
		error_message "'$1' is not install on your machine"
	fi
}

error_message() {
	echo $1
	exit
}

check_argument_specified
check_version_format
check_branch
update_version
commit_tag
build
checksum
error_message "Build and checksum can be found in 'dist' folder"
