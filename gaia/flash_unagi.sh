#! /usr/bin/env bash
# Link https://l10n.etherpad.mozilla.org/gaia-multilocale

localecode="it"

cd ~
. ./.profile echo $PATH

cd ~/moz/gaia/
git checkout v1-train
git reset --hard
git pull
cd locales/$localecode
hg pull -u
cd ../..

make clean && make production MAKECMDGOALS=production MOZILLA_OFFICIAL=1 GAIA_DEFAULT_LOCALE=$localecode LOCALES_FILE=locales/languages_all.json LOCALE_BASEDIR=locales/ REMOTE_DEBUGGER=1
