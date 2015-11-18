#! /usr/bin/env python

import argparse
import json
import urllib2

def main():
    # Parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Filename to analyze (e.g. firefox/new.lang)')
    args = parser.parse_args()

    # URL to extract activated pages and tags from langchecker's JSON
    api_url = 'http://l10n.mozilla-community.org/~pascalc/langchecker/' + \
        '?locale=all&website=0&json&file=' + args.filename

    try:
        response = urllib2.urlopen(api_url)
        json_data = json.load(response)
        file_data = json_data[args.filename]

        tag_analysis = {}
        available_tags = []

        activated_locales = []
        for locale in file_data:
            if file_data[locale]['activated']:
                tag_analysis[locale] = ['active']
                activated_locales.append(locale)
                tags = file_data[locale]['tags']
                for tag in tags:
                    if not tag in available_tags:
                        available_tags.append(tag)
                    tag_analysis[locale].append(tag)

        available_tags.sort()

        # Activated locales without tags
        no_tags_locales = []
        for locale in activated_locales:
            if len(tag_analysis[locale]) == 1:
                no_tags_locales.append(locale)
        if no_tags_locales:
            print '\nLocales activated without any addition tags (%s)' % \
                len(no_tags_locales)
            no_tags_locales.sort()
            print ', '.join(no_tags_locales)

        for tag in available_tags:
            tagged_locales = []
            non_tagged_locales = []
            for locale in activated_locales:
                if tag in tag_analysis[locale]:
                    tagged_locales.append(locale)
                else:
                    non_tagged_locales.append(locale)
            if tagged_locales:
                print '\nLocales with tag "%s" (%s)' % \
                    (tag, len(tagged_locales))
                tagged_locales.sort()
                print ', '.join(tagged_locales)
            if non_tagged_locales:
                print '\nLocales without tag "%s" (%s)' % \
                    (tag, len(non_tagged_locales))
                non_tagged_locales.sort()
                print ', '.join(non_tagged_locales)

        #print json.dumps(tag_analysis, sort_keys=True, indent=4)
    except Exception as e:
    	print 'Error reading JSON file from ' + api_url
    	print e


if __name__ == '__main__':
    main()
