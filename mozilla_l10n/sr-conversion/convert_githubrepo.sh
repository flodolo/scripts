#! /usr/bin/env bash

if [ $# -ne 1 ]
then
    echo "ERROR: no arguments supplied."
    echo "Usage: convert_githubrepo.sh [repository_folder]"
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

# Create branch and push
git branch $current_date
git checkout $current_date
git push origin $current_date

# Get a list of .po files available in sr/LC_MESSAGES
files=(locale/sr/LC_MESSAGES/*.po)
for file in ${files[@]}
do
    latin_file="${file/sr\//sr_Latn/}"
    /usr/local/opt/icu4c/bin/uconv -x Serbian-Latin/BGN -o $latin_file $file
    git add $latin_file
done

# Add change to git
git commit -a -m "Script conversion from Serbian Cyrillic to Latin ($current_date)"
git push -u origin $current_date
