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

BASE_FOLDER="/Users/flodolo/mozilla/mercurial/"

REPOSITORIES=(
    "ssh://hg.mozilla.org/l10n-central/it/"
    "ssh://hg.mozilla.org/releases/l10n/mozilla-aurora/it/"
    "ssh://hg.mozilla.org/releases/l10n/mozilla-beta/it/"
    "ssh://hg.mozilla.org/gaia-l10n/it/"
    "ssh://hg.mozilla.org/gaia-l10n/en-US/"
    "ssh://hg.mozilla.org/releases/gaia-l10n/v2_0/it/"
    "ssh://hg.mozilla.org/releases/gaia-l10n/v2_1/it/"
    "https://gaia-l10n.allizom.org/integration/gaia-2_2"
    "ssh://hg@bitbucket.org/flod/gaia-master-it"
    "https://gaia-l10n.allizom.org/integration/gaia-central"
    "ssh://hg.mozilla.org/mozilla-central"
)

FOLDER_NAMES=(
	"l10n-central"
	"mozilla-aurora"
	"mozilla-beta"
	"gaia"
	"gaia-enus"
	"gaia_v2_0"
    "gaia_v2_1"
    "gaia_v2_2"
	"gaia-master-it"
	"gaia-master-enus"
	"mozilla-central"
)

cd "$BASE_FOLDER"
for i in "${!FOLDER_NAMES[@]}"; do
  REPOSITORY="${REPOSITORIES[$i]}"
  FOLDER_NAME="${FOLDER_NAMES[$i]}"
  if [ ! -d $FOLDER_NAME ]
  	then
  		echored "Repository $FOLDER_NAME does not exist"
  		echogreen "Checking out the repo $FOLDER_NAME..."
  		hg clone $REPOSITORY $FOLDER_NAME
  	else
  		echogreen "Updating $FOLDER_NAME..."
  		hg -R $FOLDER_NAME pull -u default
  fi
done

# Extract strings in mc-strings repository
MC=~/mozilla/mercurial/mozilla-central
REPO=~/mozilla/mercurial/mc-strings
FILEMAP=~/github/scripts/mac/filemap.txt

hg convert --filemap $FILEMAP $MC $REPO
hg -R $REPO update --check
hg -R $REPO push ssh://hg@bitbucket.org/flod/mozilla-central-strings
