#! /usr/bin/env python

import json
import os
import re
import subprocess
from time import localtime, strftime

def main():

    # Path to repository folder and output json file
    path = '/home/flod/git/webstatus'
    json_filename = '/home/flod/public_html/webstatus/webstatus.json'
    # path = '/home/flodolo/mozilla/test_webstatus'
    # json_filename = '/home/flodolo/mozilla/test_webstatus/webstatus.json'
    json_data = {}
    ignored_folders = ['dbg', 'templates', '.svn', '.git']

    # Define all products that we need to check
    products = {}
    products['affiliates'] = {
        'repository_name': 'affiliates',
        'product_name': 'affiliates',
        'displayed_name': 'Firefox Affiliates',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/affiliates/',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['browserid'] = {
        'repository_name': 'browserid',
        'product_name': 'browserid',
        'displayed_name': 'Browser ID',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/browserid/',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['browserid-bigtent'] = {
        'repository_name': 'browserid-bigtent',
        'product_name': 'browserid-bigtent',
        'displayed_name': 'Browser ID Big Tent',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/browserid-bigtent/',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['browserid-bigtent-gmail'] = {
        'repository_name': 'browserid-bigtent',
        'product_name': 'browserid-bigtent-gmail',
        'displayed_name': 'Browser ID Big Tent (gmail.po)',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/browserid-bigtent/',
        'po_file': 'LC_MESSAGES/gmail.po',
        'locale_folder': 'locale'
    }
    products['browserid-client'] = {
        'repository_name': 'browserid',
        'product_name': 'browserid-client',
        'displayed_name': 'Browser ID (client.po)',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/browserid/',
        'po_file': 'LC_MESSAGES/client.po',
        'locale_folder': 'locale'
    }
    products['commbadge'] = {
        'repository_name': 'commbadge',
        'product_name': 'commbadge',
        'displayed_name': 'CommBadge',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/commbadge',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['firefoxflicks'] = {
        'repository_name': 'firefoxflicks',
        'product_name': 'firefoxflicks',
        'displayed_name': 'Firefox Flicks',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/firefoxflicks/',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['fireplace'] = {
        'repository_name': 'fireplace',
        'product_name': 'fireplace',
        'displayed_name': 'Fireplace',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/fireplace',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['fxaccount-client'] = {
        'repository_name': 'fxa-content-server-l10n',
        'product_name': 'fxaccount-client-l10n',
        'displayed_name': 'Firefox Account (client)',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/fxa-content-server-l10n',
        'po_file': 'LC_MESSAGES/client.po',
        'locale_folder': 'locale'
    }
    products['fxaccount-server'] = {
        'repository_name': 'fxa-content-server-l10n',
        'product_name': 'fxaccount-server-l10n',
        'displayed_name': 'Firefox Account (server)',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/fxa-content-server-l10n',
        'po_file': 'LC_MESSAGES/server.po',
        'locale_folder': 'locale'
    }
    products['input'] = {
        'repository_name': 'input',
        'product_name': 'input',
        'displayed_name': 'Firefox Input',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/input/',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['mozillians'] = {
        'repository_name': 'mozillians',
        'product_name': 'mozillians',
        'displayed_name': 'Mozillians',
        'repository_type': 'svn',
        'repository_url': 'http://svn.mozilla.org/projects/l10n-misc/trunk/mozillians/',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locales'
    }
    products['rocketfuel'] = {
        'repository_name': 'rocketfuel',
        'product_name': 'rocketfuel',
        'displayed_name': 'RocketFuel',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/rocketfuel',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['stats'] = {
        'repository_name': 'marketplace-stats',
        'product_name': 'marketplace-stats',
        'displayed_name': 'Marketplace Stats',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/marketplace-stats',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['webpay'] = {
        'repository_name': 'webpay',
        'product_name': 'webpay',
        'displayed_name': 'WebPay',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/webpay',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['zamboni'] = {
        'repository_name': 'zamboni',
        'product_name': 'zamboni',
        'displayed_name': 'AMO (zamboni)',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/zamboni',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    products['zamboni-js'] = {
        'repository_name': 'zamboni',
        'product_name': 'zamboni-js',
        'displayed_name': 'AMO (zamboni js)',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/zamboni',
        'po_file': 'LC_MESSAGES/javascript.po',
        'locale_folder': 'locale'
    }
    products['zippy'] = {
        'repository_name': 'zippy',
        'product_name': 'zippy',
        'displayed_name': 'Zippy',
        'repository_type': 'git',
        'repository_url': 'https://github.com/mozilla/zippy',
        'po_file': 'LC_MESSAGES/messages.po',
        'locale_folder': 'locale'
    }
    # Check if repositories exist and pull, if not clone
    for key,product in products.iteritems():
        if os.path.isdir(path + '/' + product['repository_name']):
            os.chdir(path + '/' + product['repository_name'])
            print 'Updating repository: ' + product['displayed_name']
            if (product['repository_type'] == 'git'):
                # git repository
                cmd_status = subprocess.check_output(
                    'git pull',
                    stderr = subprocess.STDOUT,
                    shell = True)
                print cmd_status
            else:
                # svn repository
                cmd_status = subprocess.check_output(
                    'svn up',
                    stderr = subprocess.STDOUT,
                    shell = True)
                print cmd_status
        else:
            os.chdir(path)
            print 'Cloning repository:' + product['repository_url']
            if (product['repository_type'] == 'git'):
                # git repository
                cmd_status = subprocess.check_output(
                    'git clone ' + product['repository_url'],
                    stderr = subprocess.STDOUT,
                    shell = True)
                print cmd_status
            else:
                # svn repository
                cmd_status = subprocess.check_output(
                    'svn co ' + product['repository_url'],
                    stderr = subprocess.STDOUT,
                    shell = True)
                print cmd_status

    for key,product in products.iteritems():
        product_folder = os.path.join(path, product['repository_name'], product['locale_folder'])
        for locale in sorted(os.listdir(product_folder)):
            # Ignore files, just folders, and ignore some of them based on ignore_folders
            locale_folder = os.path.join(product_folder, locale)
            if (os.path.isdir(locale_folder)) & (locale not in ignored_folders):
                print locale_folder
                error_status = False
                error_message = ''
                try:
                    cmd = 'msgfmt --statistics ' + locale_folder + '/' +product['po_file']
                    translation_status = subprocess.check_output(
                        cmd,
                        stderr = subprocess.STDOUT,
                        shell = True)
                except Exception as e:
                    print 'Error running msgfmt on ' + locale
                    translation_status = '0 translated messages, 9999 untranslated messages.'
                    error_status = True
                    error_message = 'Error extracting data with msgfmt --statistics'

                pretty_locale = locale.replace('_', '-')
                print 'Locale: ' + pretty_locale
                print translation_status

                # The resulting string can be something like
                # 2452 translated messages, 1278 fuzzy translations, 1262 untranslated messages.
                # 0 translated messages, 4992 untranslated messages.
                # 4992 translated messages.
                # Translated messages is always present
                search_result = re.search(r'([0-9]*) translated message', translation_status)
                try:
                    string_translated = int(search_result.group(1))
                except Exception as e:
                    string_translated = 0
                    error_status = True
                    error_message += 'Error extracting number of translated strings. '
                    print error_message
                    print e

                # Untranslated messages
                search_result = re.search(r'([0-9]*) untranslated message', translation_status)
                if search_result:
                    try:
                        string_untranslated = int(search_result.group(1))
                    except Exception as e:
                        string_untranslated = 0
                        error_status = True
                        error_message += 'Error extracting number of translated strings. '
                        print error_message
                        print e
                else:
                    string_untranslated = 0

                # Fuzzy messages
                search_result = re.search(r'([0-9]*) fuzzy translation', translation_status)
                if search_result:
                    try:
                        string_fuzzy = int(search_result.group(1))
                    except Exception as e:
                        string_fuzzy = 0
                        error_status = True
                        error_message += 'Error extracting number of fuzzy strings. '
                        print error_message
                        print e
                else:
                    string_fuzzy = 0

                string_total = string_translated + string_untranslated + string_fuzzy
                if (string_untranslated == 0) & (string_fuzzy == 0):
                    # No untranslated or fuzzy strings, locale is complete
                    complete = True
                    percentage = 100
                else:
                    # Need to calculate the completeness
                    complete = False
                    percentage = round((float(string_translated) / string_total) * 100, 1)

                if (string_untranslated == 9999):
                    # There was a problem running msgfmt. Set complete to
                    # false and string_untranslated and string_total to 0
                    complete = False
                    string_untranslated = 0
                    string_total = 0

                status_record = {
                    'name': product['displayed_name'],
                    'total': string_total,
                    'untranslated': string_untranslated,
                    'translated': string_translated,
                    'fuzzy': string_fuzzy,
                    'complete': complete,
                    'percentage': percentage,
                    'error_status': error_status,
                    'error_message': error_message
                }

                # If the pretty_locale key does not exist, I create it
                if (pretty_locale not in json_data):
                    json_data[pretty_locale] = {}
                json_data[pretty_locale][product['product_name']] = {}
                json_data[pretty_locale][product['product_name']] = status_record


    # Write back updated json data
    json_file = open(json_filename, 'w')
    json_file.write(json.dumps(json_data, sort_keys=True))
    json_file.close()

if __name__ == '__main__':
    main()
