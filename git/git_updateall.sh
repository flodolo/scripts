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

if [ "$updateall" == 'y' ] || [ "$updateall" == '' ]
then
	for folder in $(find . -mindepth 1 -maxdepth 1 -type d  \( ! -iname ".*" \) | sed 's|^\./||g');
	do
		if [ -d "./${folder}/.git" ]
		then
			# It's a git repository
            cd $folder
            green "-------------------"
            green "Updating ${folder}...."
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
                # Fetch tags
                git fetch upstream 'refs/tags/*:refs/tags/*'
                git push
            fi

			cd ..
		else
			# Not a git repository
			echo "----------"
			yellow "${folder}: not a git repository."
		fi
	done
fi
