#! /usr/bin/env bash

function interrupt_code()
# This code runs if user hits control-c
{
  echored "\n*** Setup interrupted ***\n"
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

base_folder="/Users/flodolo/mozilla/mercurial/"

repositories=(
    "ssh://hg.mozilla.org/l10n-central/it/"
    "ssh://hg.mozilla.org/releases/l10n/mozilla-beta/it/"
    "https://hg.mozilla.org/mozilla-unified"
    "https://hg.mozilla.org/hgcustom/version-control-tools"
    "https://hg.mozilla.org/l10n/compare-locales/"
    "https://hg.mozilla.org/users/axel_mozilla.com/gecko-strings-quarantine"
)

folder_names=(
	"l10n-central"
	"mozilla-beta"
	"mozilla-unified"
    "version-control-tools"
    "compare-locales"
    "gecko-strings-quarantine"
)

cd "${base_folder}"
for i in "${!folder_names[@]}"; do
  repository="${repositories[$i]}"
  folder_name="${folder_names[$i]}"
  if [ ! -d ${folder_name} ]
  	then
  		echored "Repository ${folder_name} does not exist"
  		echogreen "Checking out the repo ${folder_name}..."
  		hg clone ${repository} ${folder_name}
  	else
  		echogreen "Updating ${folder_name}..."
        if [ "${folder_name}" == "mozilla-unified" ]
            then
                # For mozilla-unified I need to update to central bookmark too
                hg -R ${folder_name} update -C
                hg -R ${folder_name} update central
                hg -R ${folder_name} pull -u
  		    else
                hg -R ${folder_name} pull -r default -u
            fi
  fi
done
