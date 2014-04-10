#! /usr/bin/env bash

echo 'Files with BOM:'
find . -type f -iname '*.lang' -print0 | xargs -0r awk '/^\xEF\xBB\xBF/ {print FILENAME} {nextfile}'

echo 'Cleaning up:'
find . -type f -iname '*.lang' -exec sed -i -e '1s/^\xEF\xBB\xBF//' {} \;

echo '----------------------'
echo 'Checking again. Files with BOM:'
find . -type f -iname '*.lang' -print0 | xargs -0r awk '/^\xEF\xBB\xBF/ {print FILENAME} {nextfile}'
