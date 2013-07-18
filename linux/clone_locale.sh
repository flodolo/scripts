#! /usr/bin/env bash

if [ "$#" -ne 1 ]
then
    # Missing parameter
    echo "ERROR: missing parameter (locale code)."
    echo "Example: clone_locale.sh it"
    exit 1
fi

localecode=$1

mkdir $localecode
cd $localecode
echo "Cloning l10n-central for $localecode"
hg clone ssh://hg.mozilla.org/l10n-central/$localecode l10n-central
echo "Cloning mozilla-aurora for $localecode"
hg clone ssh://hg.mozilla.org/releases/l10n/mozilla-aurora/$localecode/ mozilla-aurora
echo "Cloning mozilla-beta for $localecode"
hg clone ssh://hg.mozilla.org/releases/l10n/mozilla-beta/$localecode/ mozilla-beta