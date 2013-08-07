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
          <style type="text/css">
            body {background-color: #f9f9f9; font-family: Arial, Verdana; font-size: 14px; padding: 10px 30px;}
            p {margin-top: 2px;}
            table {padding: 0; margin: 0; border-collapse: collapse; color: #333; background: #F3F5F7;}
            table a {color: #3A4856; text-decoration: none; border-bottom: 1px solid #C6C8CB;}
            table a:visited {color: #777;}
            table a:hover {color: #000;}
            table thead th {background: #3A4856; padding: 15px 10px; color: #fff; text-align: center; font-weight: normal; vertical-align: top;}
            table .firstsection {padding-left: 40px; border-left: 1px solid #555;}
            table .lastsection {padding-right: 40px; border-right: 1px solid #555;}
            table tbody, table thead {border-left: 1px solid #EAECEE; border-right: 1px solid #EAECEE;}
            table tbody {border-bottom: 1px solid #EAECEE;}
            table tbody td, table tbody th {padding: 5px 20px; text-align: left;}
            table tbody tr {background: #F5F5F5;}
            table tbody tr.odd {background: #F0F2F4;}
            table tbody tr:hover {background: #EAECEE; color: #111;}
            table tbody tr.fixed {background: #A5FAB0;}
            table tbody td.number {text-align: center;}
            table tbody td.complete {background-color: #C2FCDD}
            table tbody td.incomplete {background-color: #FF9191}
          </style>
        </head>
        <body>
            <table>
              <thead>
                <tr>
                    <th>&nbsp;</th>
                    <th colspan="4">Fireplace</th>
                    <th colspan="4">Webpay</th>
                    <th colspan="4">Zamboni</th>
                <tr>
                    <th>Locale</th>
                    <th class="firstsection">Translated<br/>strings</th>
                    <th>Untranslated<br/>strings</th>
                    <th>Fuzzy<br/>strings</th>
                    <th class="lastsection">%</th>
                    <th class="firstsection">Translated<br/>strings</th>
                    <th>Untranslated<br/>strings</th>
                    <th>Fuzzy<br/>strings</th>
                    <th class="lastsection">%</th>
                    <th class="firstsection">Translated<br/>strings</th>
                    <th>Untranslated<br/>strings</th>
                    <th>Fuzzy<br/>strings</th>
                    <th class="lastsection">%</th>
                </tr>
              </thead>
              <tbody>
        '''

    for locale in sorted(json):
        html_code = html_code + "<tr>\n<td>" + locale + "</td>"
        for product in products:
            try:
                html_code = html_code + "  <td class='firstsection'>" + str(json[locale][product]['translated']) + "</td>\n"
                html_code = html_code + "  <td>" + str(json[locale][product]['untranslated']) + "</td>\n"
                html_code = html_code + "  <td>" + str(json[locale][product]['fuzzy']) + "</td>\n"
                if (json[locale][product]['complete']):
                    css_class="class='lastsection complete'"
                else:
                    css_class="class='lastsection incomplete'"
                html_code = html_code + "  <td " + css_class + ">" + str(json[locale][product]['percentage']) + "</td>\n"
            except Exception as e:
                html_code = html_code + '''  <td class='firstsection'>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td class='lastsection'>&nbsp;</td>
                '''
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

    path = "/home/flod/git/marketplace"
    products = ["fireplace", "webpay", "zamboni"]
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
                try:
                    string_translated = int(search_result.group(1))
                except Exception as e:
                    string_translated = 0
                    print "Error extracting number of translated messages"
                    print e

                # Untranslated messages
                search_result = re.search(r'([0-9]*) untranslated messages', translation_status)
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
                search_result = re.search(r'([0-9]*) fuzzy translations', translation_status)
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

    # Write back updated json data
    if (output_type == 'html') or (output_type == 'all'):
        write_html(json_data, products, html_filename)

if __name__ == "__main__":
    main()
