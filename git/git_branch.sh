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

if [ $# -lt 2 ]
  then
    red "ERROR: no arguments supplied."
    echo "Usage: git_branch.sh *repo* *branchname*"
    exit 1
fi

cd ${1}
green "-------------------"
green "Updating ${1}...."
green "-------------------"

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

if git config "branch.${2}.remote" > /dev/null
then
    red "Branch ${2} already exists, aborting."
    exit 1
fi

# Create branch
git branch ${2}
git checkout ${2}
git push origin ${2}
git branch --set-upstream-to origin/${2}
