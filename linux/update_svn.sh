#! /usr/bin/env bash

cd /home/flodolo/mozilla/svn/mozilla.com/
echo "Updating SVN repo mozilla.com" 
svn up --ignore-externals

cd /home/flodolo/mozilla/svn/l10n-misc/
echo "Updating SVN repo l10n-misc" 
svn up --ignore-externals

cd /home/flodolo/mozilla/svn/granary/
echo "Updating SVN repo granary" 
svn up --ignore-externals
