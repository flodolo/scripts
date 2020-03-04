#! /usr/bin/env python

import json
import os
import urllib2


def query_hg(locales, url):
    try:
        response = urllib2.urlopen(url)
        json_data = json.load(response)
        # hg.mozilla.org has 'entries', bitbucket 'values'
        key_name = 'values' if 'values' in json_data else 'entries'
        for repository in json_data[key_name]:
            # Ignore x-testing in mozilla.org
            if repository == 'x-testing':
                continue
            locales.append(repository['name'])
        if 'next' in json_data:
            query_hg(locales, json_data['next'])
        locales.sort()
    except Exception as e:
        print(e)


def main():
    script_folder = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    locales_hgmo = []
    try:
        url = 'https://hg.mozilla.org/l10n-central/?style=json'
        print('Reading list of l10n-central repositories')
        query_hg(locales_hgmo, url)
        # Ignore x-testing
        locales_hgmo.remove('x-testing')

        file_name = os.path.join(script_folder, 'locales_hgmo.txt')
        with open(file_name, 'w') as f:
            locales_hgmo.sort()
            for locale in locales_hgmo:
                f.write('{}\n'.format(locale))
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()
