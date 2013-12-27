#! /usr/bin/env bash

# Note: replace "ssh://" with "https://" if you don't have SSH access to hg.mozilla.org
# You need a locales.txt file in the same folder of the script

interrupt_code()
# This code runs if user hits control-c
{
  echored "*** Setup interrupted ***"
  exit $?
}

# Trap keyboard interrupt (control-c)
trap interrupt_code SIGINT

# Pretty printing functions
NORMAL=$(tput sgr0)
GREEN=$(tput setaf 2; tput bold)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)

function echored() {
    echo -e "$RED$*$NORMAL"
}

function echogreen() {
    echo -e "$GREEN$*$NORMAL"
}

function echoyellow() {
    echo -e "$YELLOW$*$NORMAL"
}

# Create "locales" folder if missing
if [ ! -d "locales" ]
then
	mkdir -p locales
fi
cd locales

for localecode in $(cat ../locales.txt)
do
	if [ -d $localecode/mozilla-beta/.hg ]
    then
		echogreen "Updating mozilla-beta for $localecode"
		hg -R $localecode/mozilla-beta pull -u default
	else
		mkdir -p $localecode
		echored "mozilla-beta for $localecode does not exist"
		cd $localecode
		echoyellow "Cloning mozilla-beta for $localecode"
		hg clone ssh://hg.mozilla.org/releases/l10n/mozilla-beta/$localecode/ mozilla-beta
		cd ..
	fi

	if [ -d $localecode/mozilla-aurora/.hg ]
    then
		echogreen "Updating mozilla-aurora for $localecode"
		hg -R $localecode/mozilla-aurora pull -u default
	else
		mkdir -p $localecode
		echored "mozilla-aurora for $localecode does not exist"
		cd $localecode
		echoyellow "Cloning mozilla-aurora for $localecode"
		hg clone ssh://hg.mozilla.org/releases/l10n/mozilla-aurora/$localecode/ mozilla-aurora
		cd ..
	fi

	if [ -d $localecode/l10n-central/.hg ]
    then
		echogreen "Updating l10n-central for $localecode"
		hg -R $localecode/l10n-central pull -u default
	else
		mkdir -p $localecode
		echored "l10n-central for $localecode does not exist"
		cd $localecode
		echoyellow "Cloning l10n-central for $localecode"
		hg clone ssh://hg.mozilla.org/l10n-central/$localecode l10n-central
		cd ..
	fi
done

