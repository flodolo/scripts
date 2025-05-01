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

base_folder="/Users/flodolo/mozilla/git/"

git_repositories=(
    "https://github.com/mozilla-firefox/firefox"
    "https://github.com/mozilla-l10n/firefox-l10n-source"
    "https://github.com/mozilla-l10n/firefox-l10n"
    "https://github.com/mozilla/compare-locales"
    "https://github.com/mozilla/fluent-migrate"
    "https://github.com/projectfluent/python-fluent"
    "https://github.com/flodolo/firefox_l10n_checks"
    "https://github.com/flodolo/mozpm_stats"
)
git_folder_names=(
    "mozilla-firefox"
    "firefox-quarantine"
    "firefox-l10n"
    "compare-locales"
    "fluent-migrate"
    "python-fluent"
    "firefox_l10n_checks"
    "mozpm_stats"
)
git_branch=(
    "main"
    "update"
    "main"
    "release"
    "main"
    "main"
    "main"
    "main"
)

cd "${base_folder}"
for i in "${!git_folder_names[@]}"
do
    repository="${git_repositories[$i]}"
    folder_name="${git_folder_names[$i]}"
    branch="${git_branch[$i]}"
    if [ ! -d "${folder_name}" ]
    then
        echored "Repository ${folder_name} does not exist"
        echogreen "Checking out the repo ${folder_name}..."
        git clone ${repository} ${folder_name}
    else
        echogreen "Updating ${folder_name}..."
    fi
    cd "${folder_name}"
    git pull
    git checkout ${branch}
    git reset --hard origin/${branch}
    cd ..
done

# Run stats
cd "${base_folder}/mozpm_stats"
git pull
./firefox_stats/extract_stats.sh "${base_folder}/firefox-quarantine/"

if [[ "$(git status --porcelain)" ]]
then
    day=$(date +"%Y%m%d")
    git add firefox_stats/db/stats.db
    git add firefox_stats/cache.json
    git commit -a -m "Update data ($day)"
    git push
fi
