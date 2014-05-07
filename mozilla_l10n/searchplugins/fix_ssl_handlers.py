#! /usr/bin/env python

''' This script assumes that localizations are stored in a
structure like the following:

this_script
    |__locales
        |__locale_code
            |__l10n-central
            |__mozilla-aurora
            |__mozilla-beta

I use this script to generate the full folder structure (all locales,
central+aurora+trunk):
https://github.com/flodolo/scripts/blob/master/mozilla_l10n/clone.sh
'''

import fileinput
import glob
import os
import shutil
import subprocess
import sys

def main():
    locales_folder = os.path.join(os.getcwd(), 'locales')
    locales = sorted(os.listdir(locales_folder))

    target_name = 'yahoo'
    target_repos = ['l10n-central', 'mozilla-aurora', 'mozilla-beta']
    target_files = [
        os.path.join('browser', 'chrome', 'browser-region', 'region.properties'),
        os.path.join('mobile', 'chrome', 'region.properties')
    ]

    # Test value overrides
    target_repos = ['mozilla-aurora']
    ##locales = ['it']

    for locale in locales:
        if not locale.startswith('.'):
            print "\n****** LOCALE: " +  locale + " ******"
            for target_repo in target_repos:
                locale_repo = os.path.join(locales_folder, locale, target_repo)
                if (os.path.isdir(locale_repo)):
                    # We have this repo, let's check searchplugins
                    status_message = "\nUpdating repo %s/%s" % (target_repo, locale)
                    subprocess.check_call(['hg','-R', locale_repo, 'pull', '-u'])
                    for target_file in target_files:
                        region_file = os.path.join(locale_repo, target_file)
                        changedfile = False

                        if os.path.isfile(region_file):
                            searchfile = fileinput.input(region_file, inplace=1)
                            # Replace http with https
                            for line in searchfile:
                                if '.uri' in line:
                                    key, value = line.split('=', 1)
                                    if ('yahoo' in value or '30boxes' in value or 'google' in value) and 'http://' in value:
                                        line = line.replace('http://', 'https://')
                                        changedfile = True
                                        status_message += "\nUpdated " + key
                                # Print updated or original line, without a new line (final comma)
                                print line,
                            searchfile.close()

                            if changedfile:
                                # Update file handler version
                                searchfile = fileinput.input(region_file, inplace=1)
                                for line in searchfile:
                                    if line.startswith('gecko.handlerService.defaultHandlersVersion'):
                                        key, value = line.split('=', 1)
                                        new_value = str(int(value) + 1)
                                        if key[-1:] == ' ':
                                            separator = ' = '
                                        else:
                                            separator = '='
                                        line = key.strip() + separator + new_value + '\n'
                                        status_message += "\nIncrement handler version to " + new_value

                                    # Print updated or original line, without a new line (final comma)
                                    print line,
                                searchfile.close()

                    # Print status
                    print status_message


if __name__ == '__main__':
    main()