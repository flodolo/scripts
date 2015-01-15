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
    echo "Usage: git_updateall.sh *path*"
    echo "Example 1: git_updateall.sh ."
    echo "Example 2: git_updateall.sh /home/user/git"
    exit 1
fi

cd $1

echo "This will check all subfolders, update them if they're git repositories (including submodules), checkout master and push to remote."
read -p "Do you want to continue (y/n, default yes)? " -n 1 updateall
echo ""

if [ "$updateall" == 'y' ] || [ "$updateall" == '' ]
then
	for folder in $(find . -mindepth 1 -maxdepth 1 -type d  \( ! -iname ".*" \) | sed 's|^\./||g');
	do
		if [ -d "./$folder/.git" ]
		then
			# It's a git repository
			echo "----------"
			green "Updating $folder..."
			cd $folder
			git stash
			git clean -fd
			git checkout master
			git fetch -p
			git fetch upstream
			git merge upstream/master
			git pull --recurse-submodules && git submodule update
			git push
			cd ..
		else
			# Not a git repository
			echo "----------"
			yellow "$folder: not a git repository."
		fi
	done
fi
