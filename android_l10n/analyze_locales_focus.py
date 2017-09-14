#! /usr/bin/env python

import argparse
import glob
import json
import os
import urllib2
import sys

def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('focus_path', help='Path to local clone of Focus for Android')
    args = parser.parse_args()

    focus_path = os.path.join(
                    os.path.realpath(args.focus_path),
                    'app', 'src', 'main', 'res')

    # Mapping some Android codes to Mozilla
    locale_mapping = {
        'in': 'id',
        'iw': 'he',
    }
    ignored_folders = ['sw600dp']

    # Get the list of locales
    locales = []
    for locale_folder in glob.glob(focus_path + '/values-*/'):
        parts = locale_folder.split(os.sep)
        # Only keep the folder name, e.g. values-it
        locale = parts[-2]
        # Split the locale code away, e.g. values-it -> it, but also values-zh-rCN -> zh-rCN
        locale = locale.split('-', 1)[1]
        # Remove -r
        locale = locale.replace('-r', '-')
        # Ignore known exclusions
        if locale in ignored_folders:
            continue
        # Map locale to Mozilla code
        locale = locale_mapping.get(locale, locale)
        locales.append(locale)
    locales.sort()

    # Get the list of complete locales
    base_url = 'https://l10n.mozilla-community.org/webstatus/api/?product=focus-android'
    update_source = base_url + '&txt&type=complete'
    response = urllib2.urlopen(update_source)
    missing_locales = []
    complete_locales = []
    for line in response:
        locale = line.rstrip('\r\n')
        complete_locales.append(locale)
        if not locale in locales:
            missing_locales.append(locale)

    complete_locales.sort()
    missing_locales.sort()
    if missing_locales:
        print('\n---\n\nThe following locales are complete but missing from the product: {}'.format(', '.join(missing_locales)))
    else:
        print('\n---\n\nThere are no complete locales missing in product.')

    incomplete_locales = diff(locales, complete_locales)
    incomplete_locales.sort()
    if incomplete_locales:
        print('\n---\n\nThe following locales are shipping but incomplete: {}'.format(', '.join(incomplete_locales)))

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
