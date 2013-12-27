#! /usr/bin/env bash

startfolder=/home/flodolo/mozilla/svn/mozilla.com/trunk/locales/
filetochange=mozorg/home.lang
stringtodelete="## promo_surfing ##"

# Get a list of folders
cd $startfolder
for locale in $(find . -mindepth 1 -maxdepth 1 -type d  \( ! -iname ".*" \) | sed 's|^\./||g');
do
	filename=$locale/$filetochange
	echo "File to change: $filename"
	echo "String to delete: $stringtodelete"
	sed -i "/$stringtodelete/d" $filename
	# If something goes wrong...
	# svn revert $filename
	echo "---------------"
done
