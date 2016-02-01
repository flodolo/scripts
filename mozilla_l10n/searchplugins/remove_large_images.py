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
    # locales = sorted(os.listdir(locales_folder))

    target_repo = 'mozilla-aurora'
    target_product = 'browser'

    # Add Pootle locales
    locales = [line.rstrip('\n') for line in open('locales_pootle.txt')]
    # Add Pontoon locales
    locales += [line.rstrip('\n') for line in open('locales_pontoon.txt')]
    # Add locales working on Mercurial but safe to add
    locales += [line.rstrip('\n') for line in open('locales_fixable.txt')]

    # locales += ['ast', 'be', 'gl', 'fy-NL', 'lij', 'mk', 'nb-NO', 'nn-NO']

    # Sort locales
    locales.sort()
    updated_locales = []

    for locale in locales:
        if not locale.startswith('.'):
            print '\n****** LOCALE: {0} ******'.format(locale)
            locale_repo = os.path.join(locales_folder, locale, target_repo)
            if (os.path.isdir(locale_repo)):
                # We have this repo, let's check searchplugins
                status_message = '\nUpdating repo {0}/{1}'.format(target_repo, locale)
                subprocess.check_call(['hg', '-R', locale_repo, 'pull', '-u'])
                subprocess.check_call(['hg', '-R', locale_repo, 'update', '-C'])
                sp_list = os.path.join(locale_repo, target_product, 'searchplugins', '*.xml')
                for sp in glob.glob(sp_list):
                    status_message += '\nAnalyzing: ' + sp
                    # Using fileinput to update file in place
                    searchfile = fileinput.input(sp, inplace=1)
                    for line in searchfile:
                        if ('width="65"' in line or 'width="130"' in line):
                            # Skip this line
                            status_message += "\nRemoved extra image."
                            if not locale in updated_locales:
                                updated_locales.append(locale)
                            continue
                        else:
                            # Print existing line, without a new line (final comma)
                            print line,
                    searchfile.close()
                # Print status
                print status_message

    if updated_locales:
        print 'List of updated locales: '
        print ', '.join(updated_locales)

if __name__ == '__main__':
    main()
