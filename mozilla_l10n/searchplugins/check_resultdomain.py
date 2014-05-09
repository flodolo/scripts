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

from __future__ import with_statement
from urlparse import urlparse
import fileinput
import glob
import os
import re
import signal
import shutil
import subprocess
import sys

def main():
    locales_folder = os.path.join(os.getcwd(), 'locales')
    locales = sorted(os.listdir(locales_folder))

    target_repos = ['l10n-central', 'mozilla-aurora']
    target_products = ['browser']

    missing_tag = []

    for locale in locales:
        if not locale.startswith('.'):
            print "\n****** LOCALE: " +  locale + " ******"
            for target_repo in target_repos:
                locale_repo = os.path.join(locales_folder, locale, target_repo)
                if (os.path.isdir(locale_repo)):
                    # We have this repo, let's check searchplugins
                    for target_product in target_products:
                        sp_list = os.path.join(locale_repo, target_product, 'searchplugins', '*.xml')
                        for sp in glob.glob(sp_list):
                            # Ignore metro searchplugins
                            if (not "metrofx" in sp):
                                searchfile = open(sp, 'r')
                                for line in searchfile:
                                    if ('url' in line.lower()) and ('type="text/html"' in line.lower()) and not ('resultdomain' in line.lower()):
                                        missing_tag.append(locale + ': ' + sp)
                                searchfile.close()

    print '\nList of wrong searchplugins: \n'
    print '\n'.join(missing_tag)


if __name__ == '__main__':
    main()

