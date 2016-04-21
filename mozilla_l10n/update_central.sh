#! /usr/bin/env bash

# Note: replace "ssh://" with "https://" if you don't have SSH access to hg.mozilla.org
# You need a locales_merge.txt file in the same folder of the script to run without parameters.
# Syntax:
# - without parameters: update all locales in locales_merge.txt
# - a list of locales to update

function interrupt_code()
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

function check_repo() {
	# $1: repository name
	# $2: locale code

	local reponame="$1"
	local localecode="$2"

	if [ -d $localecode/$reponame/.hg ]
	    then
			echogreen "Updating $reponame for $localecode"
			hg -R $localecode/$reponame pull -u default
			hg -R $localecode/$reponame update -C
            hg -R $localecode/$reponame purge
		else
			mkdir -p $localecode
			echored "$reponame for $localecode does not exist"
			cd $localecode
			echoyellow "Cloning $reponame for $localecode"
			if [ $reponame == "l10n-central" ]
			then
				hg clone ssh://hg.mozilla.org/$reponame/$localecode l10n-central
			else
				hg clone ssh://hg.mozilla.org/releases/l10n/$reponame/$localecode/ $reponame
			fi
			cd ..
		fi
}

function update_repo() {
    # $1: locale code

    local localecode="$1"

    if [ -d $localecode/l10n-central/.hg ]
        then
            echogreen "Importing mozilla-aurora changesets to l10n-central for $localecode"
            hg -R $localecode/l10n-central pull -r default $localecode/mozilla-aurora
            hg -R $localecode/l10n-central update
            hg -R $localecode/l10n-central push
        else
            echoyellow "$localecode does not have l10n-central"
        fi
}

if [ $# -ge 1 ]
then
    # Transform locale codes in an array
    locale_list="$@"
else
	# Have to update all locales
	locale_list=$(cat locales_merge.txt)
fi

# Create "locales" folder if missing
if [ ! -d "locales" ]
then
	mkdir -p locales
fi
cd locales

for localecode in $locale_list
do
	check_repo mozilla-aurora $localecode
	check_repo l10n-central $localecode
    update_repo $localecode
done
