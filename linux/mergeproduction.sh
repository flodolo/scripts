#! /usr/bin/env bash

# Original script by Pascal Chevrel (https://github.com/pascalchevrel)

# Merge stage to production for mozilla.org

production=/home/flodolo/mozilla/svn/mozilla.com/tags/production/
stage=/home/flodolo/mozilla/svn/mozilla.com/tags/stage/ 
tag=PRODUCTION

cd $production
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
svn merge $stage --ignore-ancestry -c${revision}
echo "End of merge, don't forget to commit your changes to $tag."
echo "Current status"

production+="locales"
cd $production
svn status
