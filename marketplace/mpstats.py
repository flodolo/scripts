#! /usr/bin/env python

import json
import os
import re
import subprocess
from optparse import OptionParser
from time import localtime, strftime

def write_html(json, products, filename):
    html_code = '''
        <!DOCTYPE html>
        <html lang="en-US">
        <head>
          <meta charset=utf-8>
          <title>Repo Status</title>
          <link rel="stylesheet" href="style.css" type="text/css" media="all" />
        </head>
        <body>
            <table>
              <thead>
                <tr>
                    <th>&nbsp;</th>''';

    for product in products:
        html_code = html_code + '''
                    <th colspan="3">''' + product + '''</th>
        '''

    html_code = html_code + '''<tr>
                    <th>Locale</th>'''

    for product in products:
        html_code = html_code + '''<th class="firstsection">trans.</th>
                    <th>not trans.</th>
                    <th class="lastsection">%</th>
    '''

    html_code = html_code + '''</tr>
              </thead>
              <tbody>'''

    for locale in sorted(json):
        html_code = html_code + "<tr>\n<th>" + locale + "</th>"
        for product in products:
            try:
                perc = round(json[locale][product]['percentage']/100.0, 2)
                if perc<0.30:
                    opacity = 1 - perc
                    inline_style = "style=' background-color: rgba(255, 82, 82, " + str(opacity) + ");'"
                elif perc<0.70:
                    opacity = 1.3 - perc
                    inline_style = "style=' background-color: rgba(235, 235, 110, " + str(opacity) + ");'"
                else:
                    opacity = perc
                    inline_style = "style=' background-color: rgba(146, 204, 110, " + str(opacity) + ");'"

                html_code = html_code + "  <td class='firstsection' " + inline_style + ">" + str(json[locale][product]['translated']) + "</td>\n"
                html_code = html_code + "  <td " + inline_style + ">" + str(json[locale][product]['untranslated']) + "</td>\n"
                html_code = html_code + "  <td class='lastsection' " + inline_style + ">" + str(json[locale][product]['percentage']) + "</td>\n"
            except Exception as e:
                html_code = html_code + '''  <td class='firstsection'>&nbsp;</td>
                <td>&nbsp;</td>
                <td class='lastsection'>&nbsp;</td>
                '''
                print e
                print "Product not found (" + locale + ", " + product + ")"

        html_code = html_code + "</tr>"

    html_code = html_code + '''
                </tbody>
            </table>
        <p style="padding-top: 20px;">Last update: ''' + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ''' CET</p>
    </body>
    </html>'''

    json_file = open(filename, "w")
    json_file.write(html_code)
    json_file.close()


def main():
    # Parse command line options
    clparser = OptionParser()
    clparser.add_option("-o", "--output", help="Choose a type of output", choices=["html", "json", "all"], default="all")

    (options, args) = clparser.parse_args()
    output_type = options.output

    path = "/home/flod/git/webstatus"
    products = ["fireplace", "webpay", "zamboni", "olympia", "commbadge", "rocketfuel", "marketplace-stats", "zippy"]
    json_filename = "/home/flod/public_html/mpstats/marketplace.json"
    html_filename = "/home/flod/public_html/mpstats/index.html"
    json_data = {}

    # Check if repositories exist and pull, if not clone
    for product in products:
        if os.path.isdir(path + "/" + product):
            os.chdir(path + "/" + product)
            print "Updating repository " + product
            cmd_status = subprocess.check_output(
                'git pull',
                stderr = subprocess.STDOUT,
                shell = True)
            print cmd_status
        else:
            os.chdir(path)
            print "Cloning repository https://github.com/mozilla/" + product
            cmd_status = subprocess.check_output(
                'git clone https://github.com/mozilla/' +  product,
                stderr = subprocess.STDOUT,
                shell = True)
            print cmd_status

    for product in products:
        product_folder = path + "/" + product + "/locale"

        for locale in sorted(os.listdir(product_folder)):
            # Ignore files, just folders, and ignore folder called "templates" and "dbg"
            if (os.path.isdir(os.path.join(product_folder, locale))) & (locale != "templates") & (locale != "dbg"):
                print os.path.join(product_folder, locale)

                try:
                    cmd = "msgfmt --statistics " + os.path.join(product_folder, locale) + "/LC_MESSAGES/messages.po"
                    translation_status = subprocess.check_output(
                        cmd,
                        stderr = subprocess.STDOUT,
                        shell = True)
                except Exception as e:
                    print "Error running msgfmt on " + locale
                    translation_status = "0 translated messages, 9999 untranslated messages."

                pretty_locale = locale.replace('_', '-')
                print "Locale: " + pretty_locale
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
                    print "Error extracting number of translated messages"
                    print e

                # Untranslated messages
                search_result = re.search(r'([0-9]*) untranslated message', translation_status)
                if search_result:
                    try:
                        string_untranslated = int(search_result.group(1))
                    except Exception as e:
                        string_untranslated = 0
                        print "Error extracting number of translated messages"
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
                        print "Error extracting number of translated messages"
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
    if (output_type == 'json') or (output_type == 'all'):
        json_file = open(json_filename, "w")
        json_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        json_file.close()

    # Write back html
    #if (output_type == 'html') or (output_type == 'all'):
    #   write_html(json_data, products, html_filename)

if __name__ == "__main__":
    main()
