#! /usr/bin/env bash
# Merge trunk to stage for mozilla.org
# Usage: one optional parameter (revision number)

stage=/home/flodolo/mozilla/svn/mozilla.com/tags/stage/
trunk=/home/flodolo/mozilla/svn/mozilla.com/trunk/
tag=STAGE

cd $stage
echo "----------------"
echo "Merge a revision to $tag tag for mozilla.org"

# Update the stage?
read -rp $'Do you want to svn update the repo (y/n, default yes)?\n' -n 1 updatesvn
if [ "$updatesvn" == 'y' ] || [ "$updatesvn" == '' ]
then
    echo "Updating $tag repo to the latest version..."
    svn up --ignore-externals
fi

# Which revision should I merge?
if (( $# == 1 ))
  then
    revision=$1
  else
  	read -rp $'Which revision do you want to merge?\n' revision
fi

echo "----------------"
echo "Starting merge..."
svn merge $trunk --ignore-ancestry -c${revision}
echo "End of merge, don't forget to commit your changes to $tag."
echo "Current status"

stage+="locales"
cd $stage
svn status

echo "----------------"
read -rp $'Do you want to commit your changes (y/n, default no)?\n' -n 1 commitsvn
echo "----------------"
if [ "$commitsvn" == 'y' ]
then
    echo "Commit to $tag..."
    svn ci -m "l10n: translation update"
fi
