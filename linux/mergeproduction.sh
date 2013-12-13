#! /usr/bin/env bash
# Merge stage to production for mozilla.org
# Usage: one optional parameter (revision number)

production=/home/flodolo/mozilla/svn/mozilla.com/tags/production/
stage=/home/flodolo/mozilla/svn/mozilla.com/tags/stage/
tag=PRODUCTION

cd $production
echo "----------------"
echo "Merge a revision to $tag tag for mozilla.org"
read -p "Do you want to svn update the repo (y/n, default yes)? " -n 1 updatesvn
if (( $# == 1 ))
  then
    revision=$1
  else
  	read -p "Which revision do you want to merge? " revision
  	echo ""
fi
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

echo "----------------"
read -p "Do you want to commit your changes (y/n, default no)? " -n 1 commitsvn
echo ""
echo "----------------"
if [ "$commitsvn" == 'y' ]
then
    echo "Commit to $tag..."
    svn ci -m "l10n: translation update"
fi
