#! /usr/bin/env bash

if [ $# -ne 1 ]
then
    echo "ERROR: no arguments supplied."
    echo "Usage: convert_githubrepo.sh *repo*"
    exit 1
fi

current_date=$(date +"%Y%m%d")
product_name="$1"

if [ "${product_name: -1}" == "/" ]
then
	# Remove last character "/"
	product_name="${product_name%?}"
fi

cd $product_name
# Checkout master and update
git checkout master
git fetch upstream
git merge upstream/master
git pull --recurse-submodules && git submodule update

# Branch
git branch $current_date
git checkout $current_date
git push origin $current_date

# Convert
echo "Converting strings"
if [ "$product_name" == "fxa-content-server-l10n" ]
then
	/usr/local/opt/icu4c/bin/uconv -x Serbian-Latin/BGN -o locale/sr_Latn/LC_MESSAGES/client.po locale/sr/LC_MESSAGES/client.po
	/usr/local/opt/icu4c/bin/uconv -x Serbian-Latin/BGN -o locale/sr_Latn/LC_MESSAGES/server.po locale/sr/LC_MESSAGES/server.po
	git add locale/sr_Latn/LC_MESSAGES/client.po
	git add locale/sr_Latn/LC_MESSAGES/server.po
elif [ "$product_name" == "zippy" ]
then
	/usr/local/opt/icu4c/bin/uconv -x Serbian-Latin/BGN -o locale/sr_LATN/LC_MESSAGES/messages.po locale/sr/LC_MESSAGES/messages.po
	git add locale/sr_Latn/LC_MESSAGES/messages.po
else
	/usr/local/opt/icu4c/bin/uconv -x Serbian-Latin/BGN -o locale/sr_Latn/LC_MESSAGES/messages.po locale/sr/LC_MESSAGES/messages.po
	git add locale/sr_Latn/LC_MESSAGES/messages.po
fi

# Add change to git
git commit -a -m "Script conversion from Serbian Cyrillic to Latin ($current_date)"
git push -u origin $current_date
