#! /usr/bin/env python

import json
import urllib2

def main():
    response = urllib2.urlopen('https://transvision.mozfr.org/p12n/searchplugins.json')
    json_data = json.load(response)

    output_results = []
    checked_urls = []
    print('Checking searchplugins, it will take a while.')
    for locale, locale_data in json_data['locales'].iteritems():
        for product in ['browser', 'mobile']:
            if product in locale_data:
                for sp, sp_data in locale_data[product]['trunk']['searchplugins'].iteritems():
                    if 'en-US' not in sp_data['description']:
                        url_request = sp_data['url']
                        if url_request in checked_urls:
                            continue;
                        try:
                            response = urllib2.urlopen(url_request.encode('utf8'))
                        except urllib2.HTTPError, e:
                            output_results.append(u'{} - {}: ERROR ({}). Url: {}'.format(locale, product, e.code, url_request))
                        except urllib2.URLError, e:
                            output_results.append(u'{} - {}: ERROR ({}). Url: {}'.format(locale, product, e.args, url_request))
                        checked_urls.append(url_request)

    print('\n'.join(output_results).encode('utf8'))

if __name__ == '__main__':
    main()
