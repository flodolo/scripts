#! /usr/bin/env bash

if [ $# -lt 2 ]
  then
    echo "ERROR: no arguments supplied."
    echo "Usage: git_branch.sh *repo* *branchname*"
    exit 1
fi

cd $1
git branch $2
git checkout $2
git push origin $2

