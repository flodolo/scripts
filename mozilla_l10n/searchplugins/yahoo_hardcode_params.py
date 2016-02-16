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
    locales.sort()

    target_repo = 'mozilla-aurora'
    target_products = ['browser', 'mobile']

    updated_locales = []

    replacements = {
        '<MozParam name="fr" condition="pref" pref="yahoo-fr" />': '<Param name="fr" value="moz35" />\n',
        '<MozParam name="fr" condition="pref" pref="yahoo-fr-ja" />': '<Param name="fr" value="mozff" />\n',
        '<MozParam name="nresults" condition="pref" pref="maxSuggestions" />': '<Param name="nresults" value="4" />\n'
    }

    for locale in locales:
        if not locale.startswith('.'):
            print '\n****** LOCALE: {0} ******'.format(locale)
            locale_repo = os.path.join(locales_folder, locale, target_repo)
            updated_locale = False
            if (os.path.isdir(locale_repo)):
                # We have this repo, let's check searchplugins
                for target_product in target_products:
                    status_message = ''
                    sp_list = glob.glob(os.path.join(locale_repo, target_product, 'searchplugins', 'yahoo*.xml'))
                    if sp_list and not updated_locale:
                        # Update only if this locale has Yahoo
                        status_message += '\nUpdating repo {0}/{1}'.format(target_repo, locale)
                        subprocess.check_call(['hg', '-R', locale_repo, 'pull', '-u'])
                        subprocess.check_call(['hg', '-R', locale_repo, 'update', '-C'])
                        updated_locale = True
                    for sp in sp_list:
                        status_message += '\nAnalyzing: ' + sp
                        # Using fileinput to update file in place
                        searchfile = fileinput.input(sp, inplace=1)
                        for line in searchfile:
                            replacement = replacements.get(line.strip())
                            if replacement != None:
                                indentation = len(line) - len(line.strip()) -1
                                status_message += "\nUpdated search parameter for " + target_product
                                if not locale in updated_locales:
                                    updated_locales.append(locale)
                                line = ' ' * indentation + replacement
                            # Print back line
                            print line,
                        searchfile.close()
                    # Print status
                    print status_message

    if updated_locales:
        print 'List of updated locales: '
        print ', '.join(updated_locales)

if __name__ == '__main__':
    main()
