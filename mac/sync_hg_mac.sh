#! /usr/bin/env bash

function interrupt_code()
# This code runs if user hits control-c
{
    echored "\n*** Setup interrupted ***\n"
    exit $?
}

# Trap keyboard interrupt (control-c)
trap interrupt_code SIGINT

# Pretty printing functions
NORMAL=$(tput sgr0)
GREEN=$(tput setaf 2; tput bold)
RED=$(tput setaf 1)

function echored() {
    echo -e "$RED$*$NORMAL"
}

function echogreen() {
    echo -e "$GREEN$*$NORMAL"
}

base_folder="/Users/flodolo/mozilla/mercurial/"

repositories=(
    "ssh://hg.mozilla.org/l10n-central/it/"
    "https://hg.mozilla.org/mozilla-unified"
    "https://hg.mozilla.org/hgcustom/version-control-tools"
    "https://hg.mozilla.org/l10n/compare-locales/"
    "https://hg.mozilla.org/users/francesco.lodolo_mozillaitalia.org/gecko-strings-quarantine"
    "https://hg.mozilla.org/l10n/fluent-migration"
)
folder_names=(
	"l10n-central"
	"mozilla-unified"
    "version-control-tools"
    "compare-locales"
    "gecko-strings-quarantine"
    "fluent-migration"
)

cd "${base_folder}"
for i in "${!folder_names[@]}"
do
    repository="${repositories[$i]}"
    folder_name="${folder_names[$i]}"
    if [ ! -d "${folder_name}" ]
    then
        echored "Repository ${folder_name} does not exist"
        echogreen "Checking out the repo ${folder_name}..."
        hg clone ${repository} ${folder_name}
    else
        echogreen "Updating ${folder_name}..."
        if [ "${folder_name}" == "mozilla-unified" ]
        then
            # For mozilla-unified I need to update to central bookmark too
            hg -R ${folder_name} update -C
            # Remove bookmarks
            hg -R ${folder_name} bookmarks -d central
            hg -R ${folder_name} bookmarks -d central@default
            hg -R ${folder_name} pull -u
            hg -R ${folder_name} update central
        else
            hg -R ${folder_name} pull -r default -u
        fi
    fi
done

# Git repositories
git_repositories=(
    "https://github.com/phacility/arcanist"
    "https://github.com/phacility/libphutil"
    "https://github.com/projectfluent/python-fluent"
    "https://github.com/flodolo/firefox_l10n_checks"
    "https://github.com/flodolo/mozpm_stats"
)
git_folder_names=(
    "arcanist"
    "libphutil"
    "python-fluent"
    "firefox_l10n_checks"
    "mozpm_stats"
)

cd "${base_folder}"
for i in "${!git_folder_names[@]}"
do
    repository="${git_repositories[$i]}"
    folder_name="${git_folder_names[$i]}"
    if [ ! -d "${folder_name}" ]
    then
        echored "Repository ${folder_name} does not exist"
        echogreen "Checking out the repo ${folder_name}..."
        git clone ${repository} ${folder_name}
    else
        echogreen "Updating ${folder_name}..."
        cd "${folder_name}"
        git pull
        cd ..
    fi
done

# Run stats
cd "${base_folder}/mozpm_stats"
./firefox_stats/extract_stats.sh "${base_folder}/gecko-strings-quarantine/"

if [[ "$(git status --porcelain)" ]]
then
    day=$(date +"%Y%m%d")
    git add firefox_stats/db/stats.db
    git add firefox_stats/cache.json
    git commit -a -m "Update data ($day)"
    git push
fi
