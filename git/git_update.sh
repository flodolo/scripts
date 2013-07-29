#! /usr/bin/env bash

if [ $# -lt 1 ]
  then
    echo "ERROR: no arguments supplied."
    echo "Usage: git_update.sh *repo*"
    exit 1
fi

cd $1
git checkout master
git fetch upstream
git merge upstream/master
git pull --recurse-submodules && git submodule update
git push


