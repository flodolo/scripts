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

# Create "gaia-l10n" folder if missing
if [ ! -d "gaia-l10n" ]
then
	mkdir -p gaia-l10n
fi
cd gaia-l10n

for localecode in $(cat ../locales_gaia.txt)
do
	if [ -d $localecode/.hg ]
    then
		echogreen "Updating gaia-l10n for $localecode"
		hg -R $localecode pull -u default
	else
		echoyellow "Cloning gaia-l10n for $localecode"
		hg clone ssh://hg.mozilla.org/gaia-l10n/$localecode/
	fi
done

