#! /usr/bin/env bash

echo 'Checking file encoding...'
find . -type f -name "*.lang" -exec file --mime {} + | grep -viE "utf-8|us-ascii"
