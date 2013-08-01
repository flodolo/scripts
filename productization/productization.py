#! /usr/bin/env python

# This script is designed to work inside a Transvision's folder
# (https://github.com/mozfr/transvision)

import collections
import glob
import json
import os
import re
import StringIO
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from time import gmtime, strftime
from xml.dom import minidom

# Output detail level
# 0: print only actions performed and errors extracting data from searchplugins
# 1: print errors about missing list.txt and the complete Python's error message
outputlevel = 0
clproduct = ""




def extract_sp_product(path, product, locale, channel, jsondata, splist_enUS):
    global outputlevel
    try:
        if locale != "en-US":
            # Read the list of searchplugins from list.txt
            sp_list = open(path + "list.txt", "r").read().splitlines()
            # Remove empty lines
            sp_list = filter(bool, sp_list)
            # Check for duplicates
            if (len(sp_list) != len(set(sp_list))):
                # set(sp_list) remove duplicates. If I'm here, there are
                # duplicated elements in list.txt, which is an error
                duplicated_items = [x for x, y in collections.Counter(sp_list).items() if y > 1] 
                duplicated_items_str =  ", ".join(duplicated_items)              
                print "   Error: there are duplicated items (" + duplicated_items_str + ") in list.txt (" + locale + ", " + product + ", " + channel + ")."
                
        else:
            # en-US is different: I must analyze all xml files in the folder,
            # since some searchplugins are not used in en-US but from other
            # locales
            sp_list = splist_enUS

        output = ""

        if locale != "en-US":
            # Get a list of all files inside path
            for singlefile in glob.glob(path+"*"):
                # Remove extension
                filename = os.path.basename(singlefile)
                filename_noext = os.path.splitext(filename)[0]
                if (filename_noext in splist_enUS):
                    # There's a problem: file exists but has the same name of an
                    # en-US searchplugin. Warn about this
                    print "   Error: file " + filename + " should not exist in the locale folder, same name of en-US searchplugin (" + locale + ", " + product + ", " + channel + ")."
                else:
                    # File is not in use, should be removed
                    if (filename_noext not in sp_list) & (filename != "list.txt"):
                        print "   Error: file " + filename + " not in list.txt (" + locale + ", " + product + ", " + channel + ")"

        # For each searchplugin check if the file exists (localized version) or
        # not (using en-US version)
        for sp in sp_list:
            sp_file = path + sp + ".xml"

            existingfile = os.path.isfile(sp_file)

            if (locale != "en-US") & (sp in splist_enUS) & (existingfile):
                # There's a problem: file exists but has the same name of an
                # en-US searchplugin. This file will never be picked at build
                # time, so let's analyze en-US and use it for json, acting
                # like the file doesn't exist, and print an error
                existingfile = False

            if (existingfile):
                try:
                    searchplugin_info = "(" + locale + ", " + product + ", " + channel + ", " + sp + ".xml)"

                    try:
                        xmldoc = minidom.parse(sp_file)
                    except Exception as e:
                        # Some search plugin has preprocessing instructions
                        # (#define, #if), so they fail validation. In order to
                        # extract the information I need I read the file,
                        # remove lines starting with # and parse that content
                        # instead of the original XML file
                        preprocessor = False
                        newspcontent = ""
                        for line in open(sp_file, "r").readlines():
                            if re.match("#", line):
                                # Line starts with a #
                                preprocessor = True
                            else:
                                # Line is ok, adding it to newspcontent
                                newspcontent = newspcontent + line
                        if preprocessor:
                            print "   Warning: searchplugin contains preprocessor instructions (e.g. #define, #if) that have been stripped in order to parse the XML " + searchplugin_info
                            try:
                                xmldoc = minidom.parse(StringIO.StringIO(newspcontent))
                            except Exception as e:
                                print "   Error parsing XML for searchplugin " + searchplugin_info
                                if (outputlevel > 0):
                                    print e
                        else:
                            print "   Error: problem parsing XML for searchplugin " + searchplugin_info
                            if (outputlevel > 0):
                                print e

                    # Some searchplugins use the form <tag>, others <os:tag>
                    try:
                        node = xmldoc.getElementsByTagName("ShortName")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:ShortName")
                        name = node[0].childNodes[0].nodeValue
                    except Exception as e:
                        print "   Error: problem extracting name from searchplugin " + searchplugin_info
                        name = "not available"

                    try:
                        node = xmldoc.getElementsByTagName("Description")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:Description")
                        description = node[0].childNodes[0].nodeValue
                    except Exception as e:
                        # We don't really use description anywhere, so I don't print errors
                        description = "not available"

                    try:
                        # I can have more than one url element, for example one
                        # for searches and one for suggestions
                        secure = 0

                        nodes = xmldoc.getElementsByTagName("Url")
                        if (len(nodes) == 0):
                            nodes = xmldoc.getElementsByTagName("os:Url")
                        for node in nodes:
                            if node.attributes["type"].nodeValue == "text/html":
                                url = node.attributes["template"].nodeValue
                        p = re.compile("^https://")

                        if p.match(url):
                            secure = 1
                    except Exception as e:
                        print "   Error: problem extracting url from searchplugin " + searchplugin_info
                        url = "not available"

                    try:
                        node = xmldoc.getElementsByTagName("Image")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:Image")
                        image = node[0].childNodes[0].nodeValue

                        # On mobile we can't have % characters, see for example bug 850984. Print a warning in this case
                        if (product == "mobile"):
                            if ("%" in image):
                                print "   Warning: searchplugin's image on mobile can't contain % character " + searchplugin_info

                    except Exception as e:
                        print "   Error: problem extracting image from searchplugin " + searchplugin_info
                        image = "data:image/x-icon;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAC/0lEQVR4XoWSbUiTexjG7x6d0OZW4FD3IigqaFEfJHRMt7WVGLQ9CZpR8pSiHwIZHHGdzbmzovl2tjnb8WjzBe2NCCnMFzycJ578kktwUZRDkCKhVDgouJdEn9n+/Sssy+Rc8Ptwc3FxX/z/NzQBwIBMxpsZHBx51d9fheddNeVwwHRLywV/b+/Yzfz8eMAixDicRVEPuBsbun1crkfR1FT5q/BTHI4EApQwPr53P0Inc8vLh27I5fHwyGKx+Lu60OvubuTF+Pr6WK/V+kOTKacTJs3mCn9rKzvndKL3PT1o0eOJ+qzWK8R/U1Pu8OLio/lgEDbX1mBvKMSJSUz05DU0fGkyabfD+srK+b0cTg8KhzkxsbHwMRRCywsLE3NerwuwwC2VcseNRtpnsyGmuRn9g/E6HCxjNFZjKp+YTOxkTQ2awb6/sTH6rL6e6UxP58F23dJo+KN1dfT9+npEWyzoMYax2SK0wcCOURSa0OvRc7M56jUYmNsajWArtwe26ZpYzE0rKXm4trpayBEKgWBZWF9aAi72eCkpKAowMTc8TOrn5z/AbhpQqfjXjh9/UScUotYjR9BfhYXoXnEx+levfzmgVAp+DhDbh/GGBoCEhNJ3s7MHgsvL8Mbng7fT0xAJhyGyuZklyM4+veudjJpM4CkpOX9RImGrANBn9ASBfo+JQUbM1YMH0ShFRUaqq3feyZDBAF0kWfGbWMwW4+AZTGVsbNSlVjN/HztGV3E46A8A1B4Xh9qzs9nbOt33O3lQWwsdJEmViURsKQ5SmDKCiLaqVEy3TCbokcv5nWo1fRm3qMWeFXNDJIrcJcmvTdpJsqwGh09iQ405jTe3KJWMSyr99s9tSUlcl0pFX8JNnADIjvkzOZm9c+rUWXBrtYpzaWmBMmxo8WazQsFcz83d8dqevDy+R6mkrbiJAQB1pKYGbmq1R7+YHTqdojwzc/VKfj7TJpHwYBc5ExO5bQUFtCMjI9i/Fd7CXVR0yJ6TI4D/kSMnh3/9xInDW/MnJPlM3rrfgeYAAAAASUVORK5CYII="

                    # Check if node for locale already exists
                    if (locale not in jsondata):
                        jsondata[locale] = {}
                    # Check if node for locale->product already exists
                    if (product not in jsondata[locale]):
                        jsondata[locale][product] = {}
                    # Check if node for locale->product->channel already exists
                    if (channel not in jsondata[locale][product]):
                        jsondata[locale][product][channel] = {}
                    
                    jsondata[locale][product][channel][sp] = {
                        "file": sp + ".xml",
                        "name": name,
                        "description": description,
                        "url": url,
                        "secure": secure,
                        "image": image,
                    }

                except Exception as e:
                    print "   Error: problem analyzing searchplugin " + searchplugin_info
                    if (outputlevel > 0):
                        print e
            else:
                # File does not exists, locale is using the same plugin of en-
                # US, I have to retrieve it from the dictionary
                try:
                    searchplugin_enUS = jsondata["en-US"][product][channel][sp]

                    # Check if node for locale already exists
                    if (locale not in jsondata):
                        jsondata[locale] = {}
                    # Check if node for locale->product already exists
                    if (product not in jsondata[locale]):
                        jsondata[locale][product] = {}
                    # Check if node for locale->product->channel already exists
                    if (channel not in jsondata[locale][product]):
                        jsondata[locale][product][channel] = {}

                    jsondata[locale][product][channel][sp] = {
                        "file": sp + ".xml",
                        "name": searchplugin_enUS["name"],
                        "description": "(en-US) " + searchplugin_enUS["description"],
                        "url": searchplugin_enUS["url"],
                        "secure": searchplugin_enUS["secure"],
                        "image": searchplugin_enUS["image"]
                    }                    
                except Exception as e:
                    # File does not exist but we don't have the en-US either.
                    # This means that list.txt references a non existing
                    # plugin, which will cause the build to fail
                    print "   Error: file referenced in list.txt but not available (" + locale + ", " + product + ", " + channel + ", " + sp + ".xml)"
                    if (outputlevel > 0):
                        print e                 

    except Exception as e:
        if (outputlevel > 0):
            print "  Error reading  (" + locale + ")" + path + "list.txt"




def extract_p12n_product(source, product, locale, channel, jsondata):
    global outputlevel

    try:
        # Read region.properties, ignore comments and empty lines
        values = {}
        for line in open(source):
            li = line.strip()
            if (not li.startswith("#")) & (li != ""):   
                try:        
                    # Split considering only the firs =     
                    key, value = li.split('=', 1)
                    # Remove whitespaces, some locales use key = value instead of key=value                    
                    values[key.strip()] = value.strip()
                except Exception as e:
                    print "   Error: parsing " + source + " (" + locale + ", " + product + ", " + channel + ")"            
                    if (outputlevel > 0):
                        print e
    except Exception as e:
        print "   Error: reading " + source + " (" + locale + ", " + product + ", " + channel + ")"
        if (outputlevel > 0):
            print e  

    # Check if node for locale already exists
    if (locale not in jsondata):
        jsondata[locale] = {}
    # Check if node for locale->product already exists
    if (product not in jsondata[locale]):
        jsondata[locale][product] = {}
    # Check if node for locale->product->channel already exists
    if (channel not in jsondata[locale][product]):
        jsondata[locale][product][channel] = {}    

    try:
        jsondata[locale][product][channel]["p12n"] = {
            "defaultenginename": values["browser.search.defaultenginename"]
        }
    except Exception as e:
        print "   Error: saving data from " + source + " (" + locale + ", " + product + ", " + channel + ")"               




def extract_splist_enUS (pathsource, splist_enUS):
    # Create a list of en-US searchplugins in pathsource, store this data in
    # splist_enUS
    global outputlevel
    try:
        for singlefile in glob.glob(pathsource+"*.xml"):
            filename = os.path.basename(singlefile)
            filename_noext = os.path.splitext(filename)[0]
            splist_enUS.append(filename_noext)

    except Exception as e:
        print " Error: problem reading list of en-US searchplugins from " + pathsource
        if (outputlevel > 0):
            print e




def extract_p12n_channel(pathsource, pathl10n, localeslist, channel, jsondata):
    global clproduct
    global outputlevel
    try:
        # Analyze en-US searchplugins
        print "Locale: en-US (" + channel.upper() + ")"
        path = pathsource + "COMMUN/"

        # Create a list of en-US searchplugins for each channel. If list.txt
        # for a locale contains a searchplugin with the same name of the en-US
        # one (e.g. "google"), this will have precedence. Therefore a file with
        # this name should not exist in the locale folder
        if (clproduct=="all") or (clproduct=="browser"):
            splistenUS_browser = []
            extract_splist_enUS(path + "browser/locales/en-US/en-US/searchplugins/", splistenUS_browser)
            extract_sp_product(path + "browser/locales/en-US/en-US/searchplugins/", "browser", "en-US", channel, jsondata, splistenUS_browser)
            extract_p12n_product(path + "browser/locales/en-US/en-US/chrome/browser-region/region.properties", "browser", "en-US", channel, jsondata)

        if (clproduct=="all") or (clproduct=="mobile"):
            splistenUS_mobile = []
            extract_splist_enUS(path + "mobile/locales/en-US/en-US/searchplugins/", splistenUS_mobile)
            extract_sp_product(path + "mobile/locales/en-US/en-US/searchplugins/", "mobile", "en-US", channel, jsondata, splistenUS_mobile)
            extract_p12n_product(path + "mobile/locales/en-US/en-US/chrome/region.properties", "mobile", "en-US", channel, jsondata)

        if (clproduct=="all") or (clproduct=="mail"):
            splistenUS_mail = []
            extract_splist_enUS(path + "mail/locales/en-US/en-US/searchplugins/", splistenUS_mail)
            extract_sp_product(path + "mail/locales/en-US/en-US/searchplugins/", "mail", "en-US", channel, jsondata, splistenUS_mail)
            extract_p12n_product(path + "mail/locales/en-US/en-US/chrome/messenger-region/region.properties", "mail", "en-US", channel, jsondata)

        if (clproduct=="all") or (clproduct=="suite"):
            splistenUS_suite = []
            extract_splist_enUS(path + "suite/locales/en-US/en-US/searchplugins/", splistenUS_suite)
            extract_sp_product(path + "suite/locales/en-US/en-US/searchplugins/", "suite", "en-US", channel, jsondata, splistenUS_suite)
            extract_p12n_product(path + "suite/locales/en-US/en-US/chrome/browser/region.properties", "suite", "en-US", channel, jsondata)

        locale_list = open(localeslist, "r").read().splitlines()
        for locale in locale_list:
            print "Locale: " + locale + " (" + channel.upper() + ")"
            path = pathl10n + locale + "/"
            if (clproduct=="all") or (clproduct=="browser"):
                extract_sp_product(path + "browser/searchplugins/", "browser", locale, channel, jsondata, splistenUS_browser)
                extract_p12n_product(path + "browser/chrome/browser-region/region.properties", "browser", locale, channel, jsondata)
            if (clproduct=="all") or (clproduct=="mobile"):
                extract_sp_product(path + "mobile/searchplugins/", "mobile", locale, channel, jsondata, splistenUS_mobile)
                extract_p12n_product(path + "mobile/chrome/region.properties", "mobile", locale, channel, jsondata)
            if (clproduct=="all") or (clproduct=="mail"):
                extract_sp_product(path + "mail/searchplugins/", "mail", locale, channel, jsondata, splistenUS_mail)
                extract_p12n_product(path + "mail/chrome/messenger-region/region.properties", "mail", locale, channel, jsondata)
            if (clproduct=="all") or (clproduct=="suite"):
                extract_sp_product(path + "suite/searchplugins/", "suite", locale, channel, jsondata, splistenUS_suite)
                extract_p12n_product(path + "suite/chrome/browser/region.properties", "suite", locale, channel, jsondata)
    except Exception as e:
        print "Error reading list of locales from " + localeslist
        if (outputlevel > 0):
            print e




def main():
    global clproduct

    # Parse command line options
    clparser = OptionParser()
    clparser.add_option("-p", "--product", help="Choose a specific product", choices=["browser", "mobile", "mail", "suite", "all"], default="all")
    clparser.add_option("-b", "--branch", help="Choose a specific branch", choices=["release", "beta", "aurora", "trunk", "all"], default="all")

    (options, args) = clparser.parse_args()
    clproduct = options.product
    clbranch = options.branch

    # Read configuration file
    parser = SafeConfigParser()
    parser.read("web/inc/config.ini")
    local_hg = parser.get("config", "local_hg")
    install_folder = parser.get("config", "install")

    # Set Transvision's folders and locale files
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

    jsonfilename = "web/searchplugins.json"
    jsondata = {}

    print "Last update: " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
    print "Analyzing product: " + clproduct + " - " + "branch: " + clbranch + "\n"

    if (clbranch=="all") or (clbranch=="release"):
        extract_p12n_channel(release_source, release_l10n, release_locales, "release", jsondata)
    if (clbranch=="all") or (clbranch=="beta"):
        extract_p12n_channel(beta_source, beta_l10n, beta_locales, "beta", jsondata)
    if (clbranch=="all") or (clbranch=="aurora"):
        extract_p12n_channel(aurora_source, aurora_l10n, aurora_locales, "aurora", jsondata)
    if (clbranch=="all") or (clbranch=="trunk"):
        extract_p12n_channel(trunk_source, trunk_l10n, trunk_locales, "trunk", jsondata)

    # Write back updated json data
    jsonfile = open(jsonfilename, "w")
    jsonfile.write(json.dumps(jsondata, indent=4, sort_keys=True))
    jsonfile.close()




if __name__ == "__main__":
    main()
