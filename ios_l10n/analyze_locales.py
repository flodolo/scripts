#! /usr/bin/env python

import argparse
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
    url_shipping_locales = 'https://raw.githubusercontent.com/mozilla/firefox-ios/{0}/shipping_locales.txt'.format(args.version)
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
    url_complete_locales = 'https://l10n.mozilla-community.org/webstatus/api/?product=firefox-ios&txt&type=complete'
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
    print 'NEW LOCALES'
    print 'List of locales not shipping in {0} but currently complete:'.format(args.version)
    print ', '.join(diff(complete_locales, shipping_locales))

    # List locales complete but still not shipping
    print '\nPOTENTIALLY OBSOLETE LOCALES'
    print 'List of locales shipping in {0} but currently incomplete:'.format(args.version)
    print ', '.join(diff(shipping_locales, complete_locales))

if __name__ == '__main__':
    main()
