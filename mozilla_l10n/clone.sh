#! /usr/bin/env bash

for localecode in `cat locales.txt`
do
	mkdir $localecode
	cd $localecode
	echo "Cloning mozilla-aurora for $localecode"
	hg clone ssh://hg.mozilla.org/releases/l10n/mozilla-aurora/$localecode/ mozilla-aurora
	echo "Cloning l10n-central for $localecode"
	hg clone ssh://hg.mozilla.org/l10n-central/$localecode l10n-central
	cd ..
done

