#! /usr/bin/env python

import urllib2

def read_list(url):
    locales = []
    remote_locales = urllib2.urlopen(url)
    print('Reading {0}'.format(url))
    for locale in remote_locales:
        locales.append(locale.rstrip())

    return locales

maemo_locales = read_list('https://hg.mozilla.org/mozilla-central/raw-file/default/mobile/android/locales/maemo-locales')
all_locales = read_list('https://hg.mozilla.org/mozilla-central/raw-file/default/mobile/android/locales/all-locales')

diff = list(set(all_locales) - set(maemo_locales))
diff.sort()

print '\nList of locales missing from maemo-locales:'
print '\n'.join(diff)
