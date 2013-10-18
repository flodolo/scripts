#! /usr/bin/env bash

# Reference Link: https://l10n.etherpad.mozilla.org/gaia-multilocale

localecode="it"

updatelocale=true

# One parameter from command line
if [ $# -eq 1 ] && [ $1 == '-no-update' ]
then
	updatelocale=false
fi

# This two lines force the system to read the PATH save in .profile (for adb)
cd ~
. ./.profile echo $PATH

echo ""
cd ~/moz/gaia/

if $updatelocale
then
	echo "-----------------------"
	echo "Updating Gaia"	
	git checkout v1-train
	git reset --hard
	git pull	
	echo ""
	echo "-----------------------"
	echo "Updating locale"
	cd locales/$localecode
	hg pull -u
	cd ../..
fi

make clean && PRODUCTION=1 make install-gaia MAKECMDGOALS=production MOZILLA_OFFICIAL=1 GAIA_DEFAULT_LOCALE=$localecode LOCALES_FILE=locales/languages_all.json LOCALE_BASEDIR=locales/ REMOTE_DEBUGGER=1
