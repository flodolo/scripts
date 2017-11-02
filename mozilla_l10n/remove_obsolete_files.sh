#! /usr/bin/env bash
# List of locales to ignore: da es-ES nl pl

function interrupt_code()
# This code runs if user hits control-c
{
  echored "\n*** Operation interrupted ***\n"
  exit $?
}

# Trap keyboard interrupt (control-c)
trap interrupt_code SIGINT

obsolete_files=(
    browser/chrome/browser/searchbar.dtd
    devtools/client/projecteditor.properties
    mobile/android/chrome/handling.properties
    mobile/profile/bookmarks.inc
    toolkit/chrome/global/headsUpDisplay.properties
    toolkit/chrome/mozapps/extensions/update.dtd
)

cd locales
for locale in */
do
    # Remove obsolete files
    hg --cwd ${locale} pull -u -r default
    hg --cwd ${locale} update -C
    hg --cwd ${locale} purge

    pending_changes=false
    if [ -d "${locale}/browser/chrome/browser/preferences-old" ];
    then
        hg --cwd ${locale} rm browser/chrome/browser/preferences-old
        hg --cwd ${locale} ci -m 'Bug 1349689 - Remove old preferences fork'
        pending_changes=true
    fi

    if [ -d "${locale}/embedding" ];
    then
        hg --cwd ${locale} rm embedding
        hg --cwd ${locale} ci -m 'Bug 854119 - Remove obsolete /embedding folder'
        pending_changes=true
    fi

    removed_files=false
    for file in "${obsolete_files[@]}"
    do
        if [ -f "${locale}/${file}" ];
        then
            hg --cwd ${locale} rm ${file}
            removed_files=true
        fi
    done

    if [ "$removed_files" = true ];
    then
        hg --cwd ${locale} ci -m 'Remove obsolete files'
        pending_changes=true
    fi

    if [ "$pending_changes" = true ];
    then
        hg --cwd ${locale} push
    fi
done
