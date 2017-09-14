#! /usr/bin/env python

import argparse
import json
import sys
import urllib2

def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]

def print_array(locales):
	if locales:
		print ', '.join(locales)
	else:
		print '(no locales)'

def main():
    # Parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('version', help='Branch name to check (e.g. v3.x)')
    args = parser.parse_args()

    # URL to determine the list of shipping locales in the requested branch
    url_shipping_locales = 'https://raw.githubusercontent.com/mozilla-mobile/firefox-ios/{0}/shipping_locales.txt'.format(args.version)
    try:
        shipping_locales = []
        for line in urllib2.urlopen(url_shipping_locales):
            shipping_locales.append(line.replace('\n', ''))
    except Exception as e:
        print 'Error reading {0}:'.format(url_shipping_locales), e

    if not shipping_locales:
        print 'The list of shipping locales is empty'
        sys.exit(9)

    # URL to determine the list of complete localizations
    base_url = 'https://l10n.mozilla-community.org/webstatus/api/?product=firefox-ios'
    url_complete_locales = base_url + '&txt&type=complete'
    try:
        complete_locales = []
        for line in urllib2.urlopen(url_complete_locales):
            complete_locales.append(line.replace('\n', ''))
    except Exception as e:
        print 'Error reading {0}:'.format(url_complete_locales), e

    # Add en-US
    complete_locales.append('en-US')
    complete_locales.sort()

    if not complete_locales:
        print 'The list of complete locales is empty'
        sys.exit(9)

    # List locales shipping but currently not complete
    new_locales = diff(complete_locales, shipping_locales)
    if new_locales:
        print('\n---\n\nThe following locales are complete but missing from {}: {}'.format(args.version, ', '.join(new_locales)))
    else:
        print('\n---\n\nThere are no complete locales missing in {}'.format(args.version))

    # List locales complete but still not shipping
    incomplete_locales = diff(shipping_locales, complete_locales)
    if incomplete_locales:
        print('\n---\n\nThe following locales are shipping in {} but incomplete: {}'.format(args.version, ', '.join(incomplete_locales)))
        # Get detailed stats
        update_source = base_url + '&json&type=stats'
        response = urllib2.urlopen(update_source)
        json_data = json.load(response)
        print('\nDetailed stats:')
        for locale in incomplete_locales:
            count_missing = json_data[locale]['missing'] + json_data[locale]['untranslated'] + json_data[locale]['fuzzy']
            print('{}: {} missing strings'.format(locale, count_missing))
    else:
        print('\n---\n\nThere are no incomplete locales.')


if __name__ == '__main__':
    main()
