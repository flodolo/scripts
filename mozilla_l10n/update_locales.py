#! /usr/bin/env python

import json
import os
import urllib2


def query_bitbucket(locales, url):
    try:
        response = urllib2.urlopen(url)
        json_data = json.load(response)
        for repository in json_data['values']:
            locales.append(repository['name'])
        if 'next' in json_data:
            query_bitbucket(locales, json_data['next'])
    except Exception as e:
        print(e)


def main():
    script_folder = os.path.abspath(os.path.join(os.path.dirname( __file__ )))

    locales_hgmo = []
    try:
        url = 'https://hg.mozilla.org/l10n-central/?style=raw'
        print('Reading list of l10n-central repositories')
        response = urllib2.urlopen(url)
        for line in response:
            line = line.rstrip()
            if not line:
                continue
            locales_hgmo.append(line.split('/')[-2])
        # Ignore x-testing
        locales_hgmo.remove('x-testing')

        output_file = open(os.path.join(script_folder, 'locales_hgmo.txt'), 'w')
        locales_hgmo.sort()
        for locale in locales_hgmo:
            output_file.write('{}\n'.format(locale))
        output_file.close()
    except Exception as e:
        print(e)

    locales_bitbucket = []
    try:
        url = 'https://api.bitbucket.org/2.0/repositories/mozilla-l10n'
        print('Reading list of BitBucket repositories')
        query_bitbucket(locales_bitbucket, url)
        locales_bitbucket.sort()
        output_file = open(os.path.join(script_folder, 'locales_bitbucket.txt'), 'w')
        for locale in locales_bitbucket:
            if locale in locales_hgmo:
                print('ERROR: {} is already in l10n-central, repository should be removed.'.format(locale))
                continue
            output_file.write('{}\n'.format(locale))
        output_file.close()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
