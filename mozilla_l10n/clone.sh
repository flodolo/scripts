#! /usr/bin/env bash

# Note: replace "ssh://" with "https://" if you don't have SSH access to hg.mozilla.org
# You need a locales.txt file in the same folder of the script to run without parameters.
# Syntax:
# - without parameters: update all locales listed in locales.txt
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
    # $1: locale code
    # $2: type (hgmo, bitbucket)

    local locale="$1"
    local server="$2"

    if [ -d "${locale}/.hg" ]
        then
            echogreen "Updating l10n-central for ${locale}"
            hg -R $locale pull -u -r default
            hg -R $locale update -C
            hg -R $locale purge
        else
            echored "l10n-central for ${locale} does not exist"
            echoyellow "Cloning l10n-central for ${locale}"
            if [ "${server}" == "hgmo" ]
                then
                    hg clone ssh://hg.mozilla.org/l10n-central/$locale
            elif [ "${server}" == "bitbucket" ]
                then
                    hg clone ssh://bitbucket.org/mozilla-l10n/$locale
            else
                echored "Unknown server ${server}"
            fi
        fi
}

# Create "locales" folder if missing
if [ ! -d "locales" ]
then
    mkdir -p locales
fi

if [ $# -gt 0 ]
then
    # Only update one locale and exit
    cd locales
    if [ $# -eq 1 ]
    then
        echoyellow "Assuming hgmo as provider"
        provider="hgmo"
    else
        provider="$2"
    fi
    check_repo $1 $provider
    exit
fi

# Have to update all locales
locales_hgmo=$(cat locales_hgmo.txt)
locales_bitbucket=$(cat locales_bitbucket.txt)

cd locales
for locale in $locales_hgmo
do
    check_repo $locale hgmo
done

for locale in $locales_bitbucket
do
    check_repo $locale bitbucket
done
