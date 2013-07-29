#! /usr/bin/env bash

if [ $# -lt 1 ]
  then
    echo "ERROR: no arguments supplied."
    echo "Usage: git_clone.sh *repo name*"
    echo "Example: git_clone.sh transvision will clone https://github.com/flodolo/transvision"    
    exit 1
fi

echo "Cloning https://github.com/flodolo/$1..."
git clone "https://github.com/flodolo/$1"

echo "----------------"
read -p "Do you want to add a remote (y/n, default yes)? " -n 1 addremote
if [ "$addremote" == 'y' ] || [ "$updatesvn" == '' ]
then
	cd $1
	read -p "User of remote URL? " remoteuser
    echo "Adding remote https://github.com/$remoteuser/$1..."    
    git remote add upstream https://github.com/$remoteuser/$1
fi
