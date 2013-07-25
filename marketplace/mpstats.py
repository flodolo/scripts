#! /usr/bin/env python

import json
import os
import re
import subprocess
from optparse import OptionParser

# First time you need to clone these repositories
# git clone https://github.com/mozilla/fireplace
# git clone https://github.com/mozilla/webpay
# git clone https://github.com/mozilla/zamboni

path = "/home/flodolo/pei"

def main():
    global path

    # Parse command line options
    clparser = OptionParser()
    clparser.add_option("-o", "--output", help="Choose a type of output", choices=["html", "json"], default="json")

    (options, args) = clparser.parse_args()
    output_type = options.output

    # List of products, and where I want to store the json file
    products = ["fireplace", "webpay", "zamboni"]
    json_filename = "/home/flodolo/github/transvision/web/marketplace.json"
    json_data = {}

    for product in products:
        product_folder = path + "/" + product + "/locale"

        for locale in sorted(os.listdir(product_folder)):
            # Ignore files, just folders, and ignore folder called "templates"
            if (os.path.isdir(os.path.join(product_folder, locale))) & (locale != "templates"):
                print os.path.join(product_folder, locale)

                cmd = "msgfmt --statistics " + os.path.join(product_folder, locale) + "/LC_MESSAGES/messages.po"
                translation_status = subprocess.check_output(
                    cmd,
                    stderr = subprocess.STDOUT,
                    shell = True)
                pretty_locale = locale.replace('_', '-')
                print "Locale: " + pretty_locale
                print translation_status

                # The resulting string can be something like
                # 2452 translated messages, 1278 fuzzy translations, 1262 untranslated messages.
                # 0 translated messages, 4992 untranslated messages.
                # 4992 translated messages.

                # Translated messages is always present
                search_result = re.search(r'([0-9]*) translated messages', translation_status)
                string_translated = int(search_result.group(1))

                # Untranslated messages
                search_result = re.search(r'([0-9]*) untranslated messages', translation_status)
                if search_result:
                    string_untranslated = int(search_result.group(1))
                else:
                    string_untranslated = 0

                # Fuzzy messages
                search_result = re.search(r'([0-9]*) fuzzy translations', translation_status)
                if search_result:
                    string_fuzzy = int(search_result.group(1))
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
                    percentage = round((float(string_translated) / string_total) * 100, 2)

                status_record = {
                    "total": string_total,
                    "untranslated": string_untranslated,
                    "translated": string_translated,
                    "fuzzy": string_fuzzy,
                    "complete": complete,
                    "percentage": percentage
                }

                # If the pretty_locale key does not exist, I create it
                if (pretty_locale not in json_data):
                    json_data[pretty_locale] = {}
                json_data[pretty_locale][product] = {}
                json_data[pretty_locale][product] = status_record


    # Write back updated json data
    if (output_type == 'json'):
        json_file = open(json_filename, "w")
        json_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        json_file.close()


if __name__ == "__main__":
    main()
