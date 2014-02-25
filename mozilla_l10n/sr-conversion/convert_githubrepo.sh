#! /usr/bin/env bash

if [ $# -ne 1 ]
  then
    echo "ERROR: no arguments supplied."
    echo "Usage: convert_githubrepo.sh *repo*"
    exit 1
fi

current_date=$(date +"%Y%m%d")

cd $1
# Checkout master and update
git checkout master
git fetch upstream
git merge upstream/master
git pull --recurse-submodules && git submodule update

# Branch
git branch $current_date
git checkout $current_date
git push origin $current_date

# Convert
echo "Converting strings"
/usr/local/opt/icu4c/bin/uconv -x Serbian-Latin/BGN -o locale/sr_Latn/LC_MESSAGES/messages.po locale/sr/LC_MESSAGES/messages.po

# Add change to git
git add locale/sr_Latn/LC_MESSAGES/messages.po
git commit -m "Script conversion from Serbian Cyrillic to Latin ($current_date)"
git push
