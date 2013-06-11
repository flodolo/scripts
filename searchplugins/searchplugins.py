#! /usr/bin/env python

# This script is designed to work inside a Transvision's folder
# (https://github.com/mozfr/transvision)

import glob
import json
import os
import re
from xml.dom import minidom
from optparse import OptionParser
from ConfigParser import SafeConfigParser

# Read configuration file
parser = SafeConfigParser()
parser.read("web/inc/config.ini")
local_hg = parser.get("config", "local_hg")
install_folder = parser.get("config", "install")

# Set Transvision"s folders and locale files
release_l10n = local_hg + "/RELEASE_L10N/"
beta_l10n = local_hg + "/BETA_L10N/"
aurora_l10n = local_hg + "/AURORA_L10N/"
trunk_l10n = local_hg + "/TRUNK_L10N/"

release_source = local_hg + "/RELEASE_EN-US/"
beta_source = local_hg + "/BETA_EN-US/"
aurora_source = local_hg + "/AURORA_EN-US/"
trunk_source = local_hg + "/TRUNK_EN-US/"

trunk_locales = install_folder + "/central.txt"
aurora_locales = install_folder + "/aurora.txt"
beta_locales = install_folder + "/beta.txt"
release_locales = install_folder + "/release.txt"

# Output detail level
# 0: print only actions performed and errors extracting data from searchplugins
# 1: print errors about missing list.txt and the complete Python's error message
outputlevel = 0

# Functions

def extract_sp_product(path, product, locale, channel, jsondata):
    try:
        # Read the list of searchplugins from list.txt
        sp_list = open(path + "list.txt", "r").read().splitlines()
        output = ""

        # Get a list of all files inside path
        for singlefile in glob.glob(path+'*'):
            # Remove extension
            filename = os.path.basename(singlefile)
            filename_noext = os.path.splitext(filename)[0]
            if (filename_noext not in sp_list) & (filename != "list.txt"):
                print "    File " + filename + " not in list.txt (" + locale + ", " + product + ", " + channel + ")"

        # For each searchplugin check if the file exists (localized version) or
        # not (using en-US version)
        for sp in sp_list:
            sp_file = path + sp + ".xml"
            if (os.path.isfile(sp_file)):
                try:
                    searchplugin_info = "(" + locale + ", " + product + ", " + channel + ", " + sp + ".xml)"
                    xmldoc = minidom.parse(sp_file)

                    # Some searchplugins use the form <tag>, others <os:tag>
                    try:
                        node = xmldoc.getElementsByTagName("ShortName")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:ShortName")
                        name = node[0].childNodes[0].nodeValue
                    except Exception as e:
                        print "    Error extracting name from searchplugin " + searchplugin_info
                        name = "not available"

                    try:
                        node = xmldoc.getElementsByTagName("Description")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:Description")
                        description = node[0].childNodes[0].nodeValue
                    except Exception as e:
                        # Searchplugins on mobile don't have a description, so don't print an error if the product is mobile
                        if (product != "mobile"):
                            print "    Error extracting description from searchplugin " + searchplugin_info
                        description = "not available"

                    try:
                        # I can have more than one url element, for example one
                        # for searches and one for suggestions
                        nodes = xmldoc.getElementsByTagName("Url")
                        if (len(nodes) == 0):
                            nodes = xmldoc.getElementsByTagName("os:Url")
                        for node in nodes:
                            if node.attributes["type"].nodeValue == "text/html":
                                url = node.attributes["template"].nodeValue
                        p = re.compile("^https://")
                        if p.match(url):
                            secure = 1
                        else:
                            secure = 0
                    except Exception as e:
                        print "    Error extracting url from searchplugin " + searchplugin_info
                        url = "not available"

                    try:
                        node = xmldoc.getElementsByTagName("Image")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:Image")
                        image = node[0].childNodes[0].nodeValue
                    except Exception as e:
                        print "    Error extracting image from searchplugin " + searchplugin_info
                        image = "data:image/x-icon;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAC/0lEQVR4XoWSbUiTexjG7x6d0OZW4FD3IigqaFEfJHRMt7WVGLQ9CZpR8pSiHwIZHHGdzbmzovl2tjnb8WjzBe2NCCnMFzycJ578kktwUZRDkCKhVDgouJdEn9n+/Sssy+Rc8Ptwc3FxX/z/NzQBwIBMxpsZHBx51d9fheddNeVwwHRLywV/b+/Yzfz8eMAixDicRVEPuBsbun1crkfR1FT5q/BTHI4EApQwPr53P0Inc8vLh27I5fHwyGKx+Lu60OvubuTF+Pr6WK/V+kOTKacTJs3mCn9rKzvndKL3PT1o0eOJ+qzWK8R/U1Pu8OLio/lgEDbX1mBvKMSJSUz05DU0fGkyabfD+srK+b0cTg8KhzkxsbHwMRRCywsLE3NerwuwwC2VcseNRtpnsyGmuRn9g/E6HCxjNFZjKp+YTOxkTQ2awb6/sTH6rL6e6UxP58F23dJo+KN1dfT9+npEWyzoMYax2SK0wcCOURSa0OvRc7M56jUYmNsajWArtwe26ZpYzE0rKXm4trpayBEKgWBZWF9aAi72eCkpKAowMTc8TOrn5z/AbhpQqfjXjh9/UScUotYjR9BfhYXoXnEx+levfzmgVAp+DhDbh/GGBoCEhNJ3s7MHgsvL8Mbng7fT0xAJhyGyuZklyM4+veudjJpM4CkpOX9RImGrANBn9ASBfo+JQUbM1YMH0ShFRUaqq3feyZDBAF0kWfGbWMwW4+AZTGVsbNSlVjN/HztGV3E46A8A1B4Xh9qzs9nbOt33O3lQWwsdJEmViURsKQ5SmDKCiLaqVEy3TCbokcv5nWo1fRm3qMWeFXNDJIrcJcmvTdpJsqwGh09iQ405jTe3KJWMSyr99s9tSUlcl0pFX8JNnADIjvkzOZm9c+rUWXBrtYpzaWmBMmxo8WazQsFcz83d8dqevDy+R6mkrbiJAQB1pKYGbmq1R7+YHTqdojwzc/VKfj7TJpHwYBc5ExO5bQUFtCMjI9i/Fd7CXVR0yJ6TI4D/kSMnh3/9xInDW/MnJPlM3rrfgeYAAAAASUVORK5CYII="

                    searchplugin = {
                        "file": sp + ".xml",
                        "name": name,
                        "description": description,
                        "url": url,
                        "secure": secure,
                        "image": image,
                        "locale": locale,
                        "product": product,
                        "channel": channel
                    }

                    # Example: id_record = it_browser_release_amazon-it
                    id_record = locale + "_" + product + "_" + channel + "_" + sp
                    jsondata[id_record] = searchplugin
                except Exception as e:
                    print "    Error analyzing searchplugin " + searchplugin_info
                    if (outputlevel > 0):
                        print e
            else:
                # File does not exists, locale is using the same plugin of en-
                # US, I have to retrieve it from the dictionary
                searchplugin_enUS = jsondata["en-US_" + product + "_" + channel + "_" + sp]
                searchplugin = {
                    "file": sp + ".xml",
                    "name": searchplugin_enUS["name"],
                    "description": "(en-US) " + searchplugin_enUS["description"],
                    "url": searchplugin_enUS["url"],
                    "secure": searchplugin_enUS["secure"],
                    "image": searchplugin_enUS["image"],
                    "locale": locale,
                    "product": product,
                    "channel": channel
                }
                # Example: id_record = it_browser_release_amazon-it
                id_record = locale + "_" + product + "_" + channel + "_" + sp
                jsondata[id_record] = searchplugin

    except Exception as e:
        if (outputlevel > 0):
            print "  Error reading  (" + locale + ")" + path + "list.txt"
            print e


def extract_sp_channel(pathsource, pathl10n, localeslist, channel, jsondata):
    try:
        # Analyze en-US searchplugins
        print "Analyzing en-US searchplugins on " + channel.upper()
        path = pathsource + "COMMUN/"
        extract_sp_product(path + "browser/locales/en-US/en-US/searchplugins/", "browser", "en-US", channel, jsondata)
        extract_sp_product(path + "mobile/locales/en-US/en-US/searchplugins/", "mobile", "en-US", channel, jsondata)
        extract_sp_product(path + "mail/locales/en-US/en-US/searchplugins/", "mail", "en-US", channel, jsondata)
        extract_sp_product(path + "suite/locales/en-US/en-US/searchplugins/", "seamonkey", "en-US", channel, jsondata)

        locale_list = open(localeslist, "r").read().splitlines()
        for locale in locale_list:
            print "Analyzing " + locale + " searchplugins on " + channel.upper()
            path = pathl10n + locale + "/"
            extract_sp_product(path + "browser/searchplugins/", "browser", locale, channel, jsondata)
            extract_sp_product(path + "mobile/searchplugins/", "mobile", locale, channel, jsondata)
            extract_sp_product(path + "mail/searchplugins/", "mail", locale, channel, jsondata)
            extract_sp_product(path + "suite/searchplugins/", "seamonkey", locale, channel, jsondata)
    except Exception as e:
            print "  Error reading list of locales from " + localeslist
            if (outputlevel > 0):
                print e


def main():
    jsonfilename = "web/searchplugins.json"
    jsondata = {}

    extract_sp_channel(release_source, release_l10n, release_locales, "release", jsondata)
    extract_sp_channel(beta_source, beta_l10n, beta_locales, "beta", jsondata)
    extract_sp_channel(aurora_source, aurora_l10n, aurora_locales, "aurora", jsondata)
    extract_sp_channel(trunk_source, trunk_l10n, trunk_locales, "trunk", jsondata)

    # Write back updated json data
    jsonfile = open(jsonfilename, "w")
    jsonfile.write(json.dumps(jsondata, indent=4, sort_keys=True))
    jsonfile.close()

if __name__ == "__main__":
    main()
