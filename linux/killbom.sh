#! /usr/bin/env bash

echo 'Files with BOM:'
grep -rn $'\xEF\xBB\xBF' .
echo '----------------------'

echo 'Cleaning up...'
find . -type f -exec sed -i '1 s/^\xef\xbb\xbf//' {} +

echo '----------------------'
echo 'Checking again. Files with BOM:'
grep -rn $'\xEF\xBB\xBF' .
