#! /usr/bin/env bash

interrupt_code()
# This code runs if user hits control-c
{
  echo -en "\n*** Operation interrupted ***\n"
  exit $?
}

# Trap keyboard interrupt (control-c)
trap interrupt_code SIGINT

for localecode in `cat locales.txt`
do
	echo "Updating mozilla-aurora for $localecode"
	hg -R $localecode/mozilla-aurora pull -u default
	echo "Updating l10n-central for $localecode"
	hg -R $localecode/l10n-central pull -u default
done

