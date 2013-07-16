#! /usr/bin/env bash

startfolder=/home/flodolo/mozilla/svn/mozilla.com/trunk/locales/
filetochange=firefox/update.lang

# Get a list of folders
cd $startfolder
for locale in $(find . -mindepth 1 -maxdepth 1 -type d  \( ! -iname ".*" \) | sed 's|^\./||g');
do
	stringtoadd="# Update page available at url: https://www-dev.allizom.org/b/$locale/firefox/update/"
	filename=$locale/$filetochange
	echo "File to change: $filename"
	echo "String to add: $stringtoadd"
	printf "$stringtoadd\n" | cat - $filename > temp && mv temp $filename
	# If something goes wrong...
	# svn revert $filename
	echo "---------------"    
done
