#! /usr/bin/env bash

# Reference Link: https://l10n.etherpad.mozilla.org/gaia-multilocale
# This script can be used to flash a version of Gaia greater than 1.2 on a device
# 1. Search for a folder called "gaia". If not available, clone Gaia
# repository.
# 2. If locales/XX exists, check the default repo and delete this
# folder if it doesn't match the requested version.
# 3. If locales/XX does not exist, clone the Hg locale repository.

# Syntax:
# parameter 1: version of Gaia to use (e.g. master, 1.2, 1.3)
# parameter 2: --no-update to use local information without update repos

# Change you locale code here
localecode="it"
# Folder used to store Gaia and locale repositories
repofolder="$HOME/moz/"

# You shouldn't need to modify the script after this line

function interrupt_code()
# This code runs if user hits control-c
{
  echored "\n*** Operation interrupted ***\n"
  exit $?
}

# Trap keyboard interrupt (control-c)
trap interrupt_code SIGINT

# Pretty printing functions
NORMAL=$(tput sgr0)
GREEN=$(tput setaf 2; tput bold)
RED=$(tput setaf 1)

function echored() {
    echo -e "$RED$*$NORMAL"
}

function echogreen() {
    echo -e "$GREEN$*$NORMAL"
}

function printUsage() {
	echo "Usage: flash_gaia.sh version [--no-update]"
	echo "Examples:"
	echo "flash_gaia.sh 1.2"
	echo "flash_gaia.sh 1.2 --no-update"
}

# No parameters
if [ $# -lt 1 ]
then
	echored "Script requires at least one parameter (Gaia version)."
	printUsage
	exit
fi

# Too many parameters
if [ $# -gt 2 ]
then
	echored "Too many parameters."
	printUsage
	exit
fi

if [ $# -eq 1 ]
then
	# One parameter
	if [ $1 == "--no-update" ]
	then
		echored "Missing Gaia version."
		printUsage
		exit
	else
		version="$1"
		echogreen "Flashing Gaia $version with updates"
		updatelocal=true
	fi
else
	# Two parameters
	if [ $1 == "--no-update" ]
	then
		version="$2"
		echogreen "Flashing Gaia $version without updates"
		updatelocal=false
	else
		if [ $2 == "--no-update" ]
		then
			version="$1"
			echogreen "Flashing Gaia $version without updates"
			updatelocal=false
		else
			echored "Wrong parameters"
			printUsage
		fi
	fi
fi

# Check if the provided version makes sense
if [ $version != 'master' ] && [ ${version:0:2} != '1.' ]
then
	echored "Unknown Gaia version, aborting."
	exit
fi

if [ $version == 'master' ]
then
	hggaiaversion="master"
	gitversion="master"
else
	# Replace . with _ (e.g. 1.3=>1_3) for Hg URL
	hggaiaversion=$(echo $version | tr '.' '_')
	gitversion="v$version"
fi

cd "$repofolder"

# Check Gaia repository
if [ ! -d "gaia" ]
then
	echogreen "Gaia folder not found. Cloning Gaia"
	echogreen "Cloning https://github.com/mozilla-b2g/gaia"
	git clone https://github.com/mozilla-b2g/gaia
	echogreen "Checkout $gitversion"
	git checkout $gitversion
else
	if $updatelocal
	then
		echogreen "Update Gaia repository"
		cd gaia
		echogreen "Running reset --hard"
		git reset --hard
		echogreen "Running git pull"
		echogreen "Checkout $gitversion"
		git checkout $gitversion
		git pull
	fi
fi

cd "$repofolder/gaia/locales"

# Does the locale folder exist?
if [ -d "$localecode" ]
then
	# Check which repo is cloned in the folder
	l10nrepo=$(awk -F "=" '/default/ {print $2}' $localecode/.hg/hgrc | tr -d ' ')
	echogreen "Checking if the l10n repo is correct for $gitversion"
	# If default path doesn't contain releases it's master
	if [[ $l10nrepo != *releases* ]] && [ $version != "master" ]
	then
		echored "Wrong locale version (master). Deleting folder"
		rm -r $localecode
	fi

	# If default path contains /releases/ it's a version branch
	if [[ $l10nrepo == *releases* ]] && [ $version == "master" ]
	then
		echored "Wrong locale version (not master). Deleting folder"
		rm -r $localecode
	fi
fi

# Clone if locale folder is missing
if [ ! -d "$localecode" ]
then
	# Clone locale repo
	if [ $version == 'master' ]
	then
		echogreen "Cloning https://hg.mozilla.org/gaia-l10n/$localecode/"
		hg clone https://hg.mozilla.org/gaia-l10n/$localecode/
	else
		echogreen "Cloning https://hg.mozilla.org/releases/gaia-l10n/v$hggaiaversion/$localecode/"
		hg clone https://hg.mozilla.org/releases/gaia-l10n/v$hggaiaversion/$localecode/
	fi
else
	if $updatelocal
	then
		cd $localecode
		echogreen "Update locales/$localecode repository"
		hg pull -r default
		hg up -C
	fi
fi

cd $repofolder/gaia
make clean && PRODUCTION=1 make install-gaia MAKECMDGOALS=production MOZILLA_OFFICIAL=1 GAIA_KEYBOARD_LAYOUTS=en,$localecode GAIA_DEFAULT_LOCALE=$localecode LOCALES_FILE=locales/languages_all.json LOCALE_BASEDIR=locales/ DEVICE_DEBUG=1
