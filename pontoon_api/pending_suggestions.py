#!/usr/bin/env python3

import json
import os
import sys
from urllib.parse import quote as urlquote
from urllib.request import urlopen


def main():
    # Get completion stats for locales from Pontoon
    query = '''
{
    projects {
        name
        slug
        localizations {
            locale {
                code
            },
            unreviewedStrings
        }
    }
}
'''
    pending_suggestions = {}
    try:
        print("Reading Pontoon stats...")
        url = 'https://pontoon.mozilla.org/graphql?query={}'.format(
            urlquote(query))
        response = urlopen(url)
        json_data = json.load(response)

        for project in json_data['data']['projects']:
            slug = project['slug']
            if slug in ['pontoon-intro', 'tutorial']:
                continue

            for element in project['localizations']:
                locale = element['locale']['code']
                if not locale in pending_suggestions:
                    pending_suggestions[locale] = 0
                pending_suggestions[locale] += element['unreviewedStrings']
    except Exception as e:
        print(e)

    output = []
    output.append('Locale,Pending Suggestions')
    # Only print requested locales
    for locale, suggestions in pending_suggestions.items():
        output.append('{},{}'.format(locale, pending_suggestions[locale]))

    # Save locally
    with open('output.csv', 'w') as f:
        f.write('\n'.join(output))
        print('Data stored as output.csv')

if __name__ == '__main__':
    main()
