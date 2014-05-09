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

def get_domain(url, tlds):
    # Source: http://stackoverflow.com/questions/1066933/how-to-extract-domain-name-from-url
    url_elements = urlparse(url)[1].split('.')
    # url_elements = ["abcde","co","uk"]

    for i in range(-len(url_elements), 0):
        last_i_elements = url_elements[i:]
        #    i=-3: ["abcde","co","uk"]
        #    i=-2: ["co","uk"]
        #    i=-1: ["uk"] etc

        candidate = ".".join(last_i_elements) # abcde.co.uk, co.uk, uk
        wildcard_candidate = ".".join(["*"] + last_i_elements[1:]) # *.co.uk, *.uk, *
        exception_candidate = "!" + candidate

        # match tlds:
        if (exception_candidate in tlds):
            return ".".join(url_elements[i:])
        if (candidate in tlds or wildcard_candidate in tlds):
            return ".".join(url_elements[i-1:])
            # returns "abcde.co.uk"

    # Domain not in list
    return 'xxxxxx'

def main():
    # load tlds, ignore comments and empty lines:
    with open("effective_tld_names.txt") as tld_file:
        tlds = [line.strip() for line in tld_file if line[0] not in "/\n"]

    locales_folder = os.path.join(os.getcwd(), 'locales')
    locales = sorted(os.listdir(locales_folder))

    target_repos = ['mozilla-aurora']
    target_products = ['browser']

    errors = []
    changed = []

    try:
        for locale in locales:
            if not locale.startswith('.'):
                print "\n****** LOCALE: " +  locale + " ******"
                for target_repo in target_repos:
                    locale_repo = os.path.join(locales_folder, locale, target_repo)
                    if (os.path.isdir(locale_repo)):
                        # We have this repo, let's check searchplugins
                        status_message = "\nUpdating repo %s/%s" % (target_repo, locale)
                        # Update local repo, discard changes
                        subprocess.check_call(['hg','-R', locale_repo, 'pull', '-u'])
                        subprocess.check_call(['hg','-R', locale_repo, 'update', '-C'])
                        for target_product in target_products:
                            sp_list = os.path.join(locale_repo, target_product, 'searchplugins', '*.xml')
                            for sp in glob.glob(sp_list):
                                # Ignore metro searchplugins
                                if (not "metrofx" in sp):
                                    # Using fileinput to update file in place
                                    searchfile = fileinput.input(sp, inplace=1)
                                    for line in searchfile:
                                        if ('url' in line.lower()) and ('type="text/html"' in line.lower()) and not ('resultdomain' in line.lower()):
                                            if line.rstrip('\n').endswith('>'):
                                                # Extract template URL
                                                template_url = re.search('template="(.+?)"', line).group(1)
                                                template_domain = get_domain(template_url, tlds)
                                                status_message += '\n\nAnalyzing: ' + sp
                                                status_message += "\nLine found, adding parameter (" + template_domain + ")"
                                                line = line.replace('>', ' resultdomain="' +  template_domain + '">')
                                                changed.append(locale + ': ' + sp)
                                                # Remove multiple spaces
                                                re.sub(' +', ' ', line)
                                            else:
                                                status_message += '\n\nAnalyzing: ' + sp
                                                status_message += '\nIgnoring, unexpected structure.'
                                                errors.append(locale + ': ' + sp)
                                        # Print updated or original line, without a new line (final comma)
                                        print line,
                                    searchfile.close()
                        # Print status
                        print status_message
    except KeyboardInterrupt:
        # Print errors when CTRL+C is pressed
        print '\nQuitting...\nList of ignored searchplugins: \n'
        print '\n'.join(errors)
        print '\nList of updated searchplugins: \n'
        print '\n'.join(changed)
        sys.exit()

    # Print errors anyway at the end
    print '\nQuitting...\nList of ignored searchplugins: \n'
    print '\n'.join(errors)
    print '\nList of updated searchplugins: \n'
    print '\n'.join(changed)


if __name__ == '__main__':
    main()

