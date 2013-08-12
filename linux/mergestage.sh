#! /usr/bin/env bash

# Original script by Pascal Chevrel (https://github.com/pascalchevrel)

# Merge trunk to stage for mozilla.org

stage=/home/flodolo/mozilla/svn/mozilla.com/tags/stage/
trunk=/home/flodolo/mozilla/svn/mozilla.com/trunk/
tag=STAGE

cd $stage
echo "----------------"
echo "Merge a revision to $tag tag for mozilla.org"
read -p "Which revision do you want to merge? " revision
read -p "Do you want to svn update the repo (y/n, default yes)? " -n 1 updatesvn
echo "----------------"
if [ "$updatesvn" == 'y' ] || [ "$updatesvn" == '' ]
then
    echo "Updating $tag repo to the latest version..."
    svn up --ignore-externals
fi
echo "Starting merge..."
svn merge $trunk --ignore-ancestry -c${revision}
echo "End of merge, don't forget to commit your changes to $tag."
echo "Current status"

stage+="locales"
cd $stage
svn status

echo "----------------"
read -p "Do you want to commit your changes (y/n, default no)? " -n 1 commitsvn
echo "----------------"
if [ "$commitsvn" == 'y' ]
then
    echo "Commit to $tag..."
    svn ci -m "l10n: translation update"
fi
