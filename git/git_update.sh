#! /usr/bin/env bash

# Pretty printing functions
NORMAL=$(tput sgr0)
GREEN=$(tput setaf 2; tput bold)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)

function red() {
    echo -e "$RED$*$NORMAL"
}

function green() {
    echo -e "$GREEN$*$NORMAL"
}

function yellow() {
    echo -e "$YELLOW$*$NORMAL"
}

if [ $# -lt 1 ]
  then
    red "ERROR: no arguments supplied."
    echo "Usage: git_update.sh *repo*"
    exit 1
fi

if [ ! -d "./${1}/.git" ]
then
    yellow "${1}: not a git repository."
    exit 1
fi

cd ${1}
green "-------------------"
green "Updating ${1}...."
green "-------------------"

# Remove pending changes, untracked files and folders
green "Remove pending changes and untracked files/folders..."
git reset --hard
git clean -fd

# Make sure to be on master
green "Updating master..."
git checkout master
git pull
git fetch -p

# If upstream is defined, pull and merge
if git config remote.upstream.url > /dev/null
then
    green "Fetching upstream..."
    git fetch upstream
    git merge upstream/master
    git push
fi
