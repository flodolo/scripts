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




def extract_sp_product(path, product, locale, channel, jsondata, splist_enUS):
    global outputlevel
    try:
        if locale != "en-US":
            # Read the list of searchplugins from list.txt or metrolist.txt
            if (os.path.isfile(path + "list.txt")):
                sp_list_desktop = open(path + "list.txt", "r").read().splitlines()
            else:
                print "   Warning: path to list.txt does not exists (" + locale + ", " + product + ", " + channel + ")."
                sp_list_desktop = []

            if (os.path.isfile(path + "metrolist.txt")):
                sp_list_metro = open(path + "metrolist.txt", "r").read().splitlines()
            else:
                if (product=="metro"):
                    # Display error only once when checking metro
                    print "   Warning: path to metrolist.txt does not exists (" + locale + ", " + product + ", " + channel + ")."
                sp_list_metro = []

            sp_list_complete = sp_list_metro + sp_list_desktop

            if (product == "desktop"):
                sp_list = filter(bool, sp_list_desktop)
            else:
                sp_list = filter(bool, sp_list_metro)

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
                    if (filename_noext not in sp_list_complete) & (filename != "list.txt") & (filename != "metrolist.txt"):
                        print "   Error: file " + filename + " not in list.txt or metrolist.txt (" + locale + ", " + product + ", " + channel + ")"

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
                    }

                except Exception as e:
                    print "   Error: problem analyzing searchplugin " + searchplugin_info
                    if (outputlevel > 0):
                        print e
            else:
                # File does not exists, locale is using the same plugin of en-
                # US, I have to retrieve it from the dictionary
                # Product is always "browser", no distinction between metro and desktop
                try:
                    searchplugin_enUS = jsondata["en-US"]["browser"][channel][sp]

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

    # Use jsondata to create a list of all Searchplugins' descriptions
    try:
        available_searchplugins = []
        if (channel in jsondata[locale][product]):
            # I need to proceed only if I have searchplugin for this branch+product+locale
            for element in jsondata[locale][product][channel].values():
                if element["name"]:
                    available_searchplugins.append(element["name"])

            existingfile = os.path.isfile(source)
            if existingfile:
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

                defaultenginename = '-'
                searchorder = {}

                for key, value in values.iteritems():
                    lineok = False

                    # Default search engine name. Example:
                    # browser.search.defaultenginename=Google
                    if key.startswith('browser.search.defaultenginename'):
                        lineok = True
                        defaultenginename = values["browser.search.defaultenginename"]
                        if (unicode(defaultenginename, "utf-8") not in available_searchplugins):
                            print "   Error: " + defaultenginename + " is set as default but not available in searchplugins (check if the name is spelled correctly)"

                    # Search engines order. Example:
                    # browser.search.order.1=Google
                    if key.startswith('browser.search.order.'):
                        lineok = True
                        searchorder[key[-1:]] = value
                        if (unicode(value, "utf-8") not in available_searchplugins):
                            print "   Error: " + value + " is defined in searchorder but not available in searchplugins (check if the name is spelled correctly)"

                    # I don't need this data for Metro, just ignore them
                    if ( key.startswith('browser.contentHandlers.types.') or
                         key.startswith('gecko.handlerService.defaultHandlersVersion') or
                         key.startswith('gecko.handlerService.schemes.')):
                        lineok = True


                    # Unrecognized line, print warning
                    if (not lineok):
                        print "   Warning: unknown key in region.properties: " + locale + ", " + product + ", " + channel + "."
                        print "   " + key + "=" + value

                try:
                    jsondata[locale][product][channel]["p12n"] = {
                        "defaultenginename": defaultenginename,
                        "searchorder": searchorder,
                    }
                except Exception as e:
                    print "   Error: problem saving data into json from " + source + " (" + locale + ", " + product + ", " + channel + ")"

            else:
                if (outputlevel > 0):
                    print "   Warning: file does not exist " + source + " (" + locale + ", " + product + ", " + channel + ")"
    except Exception as e:
        print "   Warning: no searchplugins available for this locale (" + product + ")"




def check_p12n(locale, channel, jsondata):
    # Check Metro status
    try:
        if ("metro" in jsondata[locale]):
            for sp in jsondata[locale]["metro"][channel]:
                if (sp != "p12n"):
                    element = jsondata[locale]["metro"][channel][sp]
                    if (element["file"] == "google.xml"):
                        print "   METROCHECK: use googlemetrofx.xml instead of google.xml"
                    if (element["file"] == "bing.xml"):
                        print "   METROCHECK: use bingmetrofx.xml instead of bing.xml"

            if ("p12n" in jsondata[locale]["metro"][channel]):
                # I have p12n for Metro
                default_metro = jsondata[locale]["metro"][channel]["p12n"]["defaultenginename"]
                default_desktop = jsondata[locale]["desktop"][channel]["p12n"]["defaultenginename"]
                if (default_desktop != default_metro):
                    print "   METROCHECK: default engine on Desktop (" + default_desktop + ") is different from default engine on Metro (" + default_metro + ")"

                order_metro = jsondata[locale]["metro"][channel]["p12n"]["searchorder"]
                order_desktop = jsondata[locale]["desktop"][channel]["p12n"]["searchorder"]
                if (default_desktop != default_metro):
                    print "   METROCHECK: search engine order on Desktop is different from Metro"
                    print "   Desktop"
                    print order_desktop
                    print "   Metro"
                    print order_metro
    except Exception as e:
        print e




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
    global outputlevel
    try:
        # Analyze en-US searchplugins
        print "\nLocale: en-US (" + channel.upper() + ")"
        path = pathsource + "COMMUN/"

        # Get a list of all .xml files in the en-US searchplugins folder (both Metro and Desktop)
        splistenUS = []
        extract_splist_enUS(path + "browser/locales/en-US/en-US/searchplugins/", splistenUS)

        # Extract searchplugins information: I need en-US only to check names
        # when a locale rely on en-US searchplugins, so I'll keep them under a
        # generic "browser" product (no need to separate "desktop" and "metro")
        extract_sp_product(path + "browser/locales/en-US/en-US/searchplugins/", "browser", "en-US", channel, jsondata, splistenUS)

        locale_list = open(localeslist, "r").read().splitlines()
        for locale in locale_list:
            print "\nLocale: " + locale + " (" + channel.upper() + ")"
            path = pathl10n + locale + "/"

            extract_sp_product(path + "browser/searchplugins/", "desktop", locale, channel, jsondata, splistenUS)
            extract_p12n_product(path + "browser/chrome/browser-region/region.properties", "desktop", locale, channel, jsondata)
            extract_sp_product(path + "browser/searchplugins/", "metro", locale, channel, jsondata, splistenUS)
            extract_p12n_product(path + "browser/metro/chrome/region.properties", "metro", locale, channel, jsondata)
            check_p12n(locale, channel, jsondata)

    except Exception as e:
        print "Error reading list of locales from " + localeslist
        if (outputlevel > 0):
            print e




def main():

    # Parse command line options
    clparser = OptionParser()
    clparser.add_option("-b", "--branch", help="Choose a specific branch", choices=["release", "beta", "aurora", "trunk", "all"], default="all")

    (options, args) = clparser.parse_args()
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
    print "Analyzing product: Firefox - " + "branch: " + clbranch + "\n"

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
