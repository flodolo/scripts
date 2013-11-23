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


def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]


def extract_sp_product(path, product, locale, channel, jsondata, splist_enUS, html_output):
    try:
        if locale != "en-US":
            # Read the list of searchplugins from list.txt or metrolist.txt
            if (os.path.isfile(path + "list.txt")):
                sp_list_desktop = open(path + "list.txt", "r").read().splitlines()
            else:
                html_output.append("<p><span class='warning'>Warning:</span> file list.txt not found in your repository.</p>")
                sp_list_desktop = []

            if (os.path.isfile(path + "metrolist.txt")):
                sp_list_metro = open(path + "metrolist.txt", "r").read().splitlines()
            else:
                if (product=="metro" and locale!='ja-JP-mac'):
                    # Display error only once when checking metro, not for ja-JP-mac
                    html_output.append("<p><span class='warning'>Warning:</span> file metrolist.txt not found in your repository.</p>")
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
                html_output.append("<p><span class='error'>Error:</span> there are duplicated items (" + duplicated_items_str + ") in list.txt (" + locale + ", " + product + ", " + channel + ").</p>")

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
                    html_output.append("<p><span class='error'>Error:</span> file " + filename + " should not exist in the locale folder, same name of en-US searchplugin (" + locale + ", " + product + ", " + channel + ").</p>")
                else:
                    # File is not in use, should be removed
                    if (filename_noext not in sp_list_complete) & (filename != "list.txt") & (filename != "metrolist.txt"):
                        html_output.append("<p><span class='error'>Error:</span> file " + filename + " not in list.txt or metrolist.txt (" + locale + ", " + product + ", " + channel + ")</p>")

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
                                html_output.append("<p class='error'>Error parsing XML for searchplugin " + searchplugin_info + "</p>")
                                print e
                        else:
                            html_output.append("<p><span class='error'>Error:</span> problem parsing XML for searchplugin " + searchplugin_info + "</p>")
                            print e

                    # Some searchplugins use the form <tag>, others <os:tag>
                    try:
                        node = xmldoc.getElementsByTagName("ShortName")
                        if (len(node) == 0):
                            node = xmldoc.getElementsByTagName("os:ShortName")
                        name = node[0].childNodes[0].nodeValue
                    except Exception as e:
                        html_output.append("<p><span class='error'>Error:</span> problem extracting name from searchplugin " + searchplugin_info + "</p>")
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
                    html_output.append("<p><span class='error'>Error:</span> problem analyzing searchplugin " + searchplugin_info + "</p>")
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
                    html_output.append("<p><span class='error'>Error:</span> file referenced in list.txt but not available (" + locale + ", " + product + ", " + channel + ", " + sp + ".xml)</p>")
                    print e

    except Exception as e:
        print "  Error reading  (" + locale + ")" + path + "list.txt"




def extract_p12n_product(source, product, locale, channel, jsondata, html_output):
    # Use jsondata to create a list of all Searchplugins' descriptions
    try:
        available_searchplugins = []

        # Check if region.properties exists
        existingfile = os.path.isfile(source)
        if (not existingfile):
            html_output.append("<p><span class='warning'>Warning:</span> file region.properties not found in your repository (" + product + ")</p>")

        if (channel in jsondata[locale][product]) and (existingfile):

            # I need to proceed only if I have searchplugin for this branch+product+locale
            for element in jsondata[locale][product][channel].values():
                if element["name"]:
                    available_searchplugins.append(element["name"])

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
                            html_output.append("<p><span class='error'>Error:</span> parsing " + source + " (" + locale + ", " + product + ", " + channel + ")</p>")
                            print e
            except Exception as e:
                html_output.append("<p><span class='error'>Error:</span> reading " + source + " (" + locale + ", " + product + ", " + channel + ")</p>")
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
                        html_output.append("<p><span class='error'>Error:</span> " + defaultenginename + " (" + product + ") is set as default but not available in searchplugins (check if the name is spelled correctly).</p>")

                # Search engines order. Example:
                # browser.search.order.1=Google
                if key.startswith('browser.search.order.'):
                    lineok = True
                    searchorder[key[-1:]] = value
                    if (unicode(value, "utf-8") not in available_searchplugins):
                        html_output.append("<p><span class='error'>Error:</span> " + value + " (" + product + ") is defined in searchorder but not available in searchplugins (check if the name is spelled correctly).</p>")

                # I don't need this data for Metro, just ignore them
                if ( key.startswith('gecko.handlerService.defaultHandlersVersion') or
                     key.startswith('gecko.handlerService.schemes.')):
                    lineok = True

                if key.startswith('browser.contentHandlers.types.'):
                    lineok = True
                    if key.endswith('.title') and (value.lower() == 'google'):
                        html_output.append("<p><span class='warning'>Warning:</span> Google Reader has been dismissed, see <a href='https://bugzilla.mozilla.org/show_bug.cgi?id=906688'>bug 906688</a> (" + key + ", " + product + ").</p>")

                # Unrecognized line, print warning
                if (not lineok):
                    html_output.append("<p><span class='warning'>Warning:</span> unknown key in region.properties (" + product + ").<br/>")
                    html_output.append("<span class='code'>" + key + "=" + value + "</span></p>")

            try:
                jsondata[locale][product][channel]["p12n"] = {
                    "defaultenginename": defaultenginename,
                    "searchorder": searchorder,
                }
            except Exception as e:
                print "   Error: problem saving data into json from " + source + " (" + locale + ", " + product + ", " + channel + ")"

    except Exception as e:
        print "No searchplugins available for this locale (" +locale + ", " + product + ")"




def check_p12n(locale, channel, jsondata, html_output):
    # Compare Metro and Desktop list of searchplugin
    try:
        metro_searchplugins = []
        desktop_searchplugins = []
        if ("metro" in jsondata[locale]):
            for sp in jsondata[locale]["metro"][channel]:
                if (sp != "p12n"):
                    element = jsondata[locale]["metro"][channel][sp]
                    if (element["file"] == "google.xml"):
                        html_output.append("<p><span class='metro'>Metro:</span> use googlemetrofx.xml instead of google.xml</p>")
                    if (element["file"] == "bing.xml"):
                        html_output.append("<p><span class='metro'>Metro:</span> use bingmetrofx.xml instead of bing.xml</p>")

                    # Strip .xml from the filename
                    searchplugin_name = element["file"][:-4]
                    # If it's a Metro version, strip "metro" from the name
                    if (searchplugin_name in ["googlemetrofx", "bingmetrofx"]):
                        searchplugin_name = searchplugin_name[:-7]
                    metro_searchplugins.append(searchplugin_name)
                    metro_searchplugins.sort()

            for sp in jsondata[locale]["desktop"][channel]:
                if (sp != "p12n"):
                    element = jsondata[locale]["desktop"][channel][sp]
                    # Strip .xml from the filename
                    searchplugin_name = element["file"][:-4]
                    desktop_searchplugins.append(searchplugin_name)
                    desktop_searchplugins.sort()

            differences = diff(metro_searchplugins, desktop_searchplugins)
            if differences:
                html_output.append("<p><span class='metro'>Metro:</span> there are differences between the searchplugins used in Metro and Desktop</p>")
                html_output.append("<p>Metro searchplugins: ")
                for element in metro_searchplugins:
                    html_output.append(element + " ")
                html_output.append("</p>")

                html_output.append("<p>Desktop searchplugins: ")
                for element in desktop_searchplugins:
                    html_output.append(element + " ")
                html_output.append("</p>")
    except Exception as e:
        print e

    # Check Metro status for region.properties
    try:
        if ("metro" in jsondata[locale]):
            if ("p12n" in jsondata[locale]["metro"][channel]):
                # I have p12n for Metro
                default_metro = jsondata[locale]["metro"][channel]["p12n"]["defaultenginename"]
                default_desktop = jsondata[locale]["desktop"][channel]["p12n"]["defaultenginename"]
                if (default_desktop != default_metro):
                    html_output.append("<p><span class='metro'>Metro:</span> default engine on Desktop (" + default_desktop + ") is different from default engine on Metro (" + default_metro + ")</p>")

                order_metro = jsondata[locale]["metro"][channel]["p12n"]["searchorder"]
                order_desktop = jsondata[locale]["desktop"][channel]["p12n"]["searchorder"]
                if (default_desktop != default_metro):
                    html_output.append("<p><span class='metro'>Metro:</span> search engine order on Metro is different from Desktop.</p>")
                    html_output.append("<p>Desktop:</p>")
                    html_output.append("  <ul>")
                    for number in sorted(order_desktop.iterkeys()):
                        html_output.append("    <li>" + number + ":" + order_desktop[number] + "</li>")
                    html_output.append("  </ul>")
                    html_output.append("<p>Metro:</p>")
                    html_output.append("  <ul>")
                    for number in sorted(order_metro.iterkeys()):
                        html_output.append("    <li>" + number + ":" + order_metro[number] + "</li>")
                    html_output.append("  </ul>")
    except Exception as e:
        print e




def extract_splist_enUS (pathsource, splist_enUS):
    # Create a list of en-US searchplugins in pathsource, store this data in
    # splist_enUS
    try:
        for singlefile in glob.glob(pathsource+"*.xml"):
            filename = os.path.basename(singlefile)
            filename_noext = os.path.splitext(filename)[0]
            splist_enUS.append(filename_noext)

    except Exception as e:
        print " Error: problem reading list of en-US searchplugins from " + pathsource
        print e




def extract_p12n_channel(pathsource, pathl10n, localeslist, channel, jsondata, html_output):
    try:
        # Analyze en-US searchplugins
        html_output.append("<h2>Locale: en-US (" + channel.upper() + ")</h2>")

        path = pathsource + "COMMUN/"

        # Get a list of all .xml files in the en-US searchplugins folder (both Metro and Desktop)
        splistenUS = []
        extract_splist_enUS(path + "browser/locales/en-US/en-US/searchplugins/", splistenUS)

        # Extract searchplugins information: I need en-US only to check names
        # when a locale rely on en-US searchplugins, so I'll keep them under a
        # generic "browser" product (no need to separate "desktop" and "metro")
        extract_sp_product(path + "browser/locales/en-US/en-US/searchplugins/", "browser", "en-US", channel, jsondata, splistenUS, html_output)

        locale_list = open(localeslist, "r").read().splitlines()
        for locale in locale_list:
            html_output.append("<h2><a id='" + locale + "' href='#" + locale + "'>Locale: " + locale + " (" + channel.upper() + ")</a></h2>")
            path = pathl10n + locale + "/"

            extract_sp_product(path + "browser/searchplugins/", "desktop", locale, channel, jsondata, splistenUS, html_output)
            extract_p12n_product(path + "browser/chrome/browser-region/region.properties", "desktop", locale, channel, jsondata, html_output)
            extract_sp_product(path + "browser/searchplugins/", "metro", locale, channel, jsondata, splistenUS, html_output)
            extract_p12n_product(path + "browser/metro/chrome/region.properties", "metro", locale, channel, jsondata, html_output)
            check_p12n(locale, channel, jsondata, html_output)

    except Exception as e:
        print "Error reading list of locales from " + localeslist
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

    htmlfilename = "web/metro.html"
    html_output = ['''<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset=utf-8>
            <title>Metro Status</title>
            <style type="text/css">
                body {background-color: #FFF; font-family: Arial, Verdana; font-size: 14px; padding: 10px;}
                p {margin-top: 2px;}
                span.warning {color: orange; font-weight: bold;}
                span.error {color: red; font-weight: bold;}
                span.metro {color: blue; font-weight: bold;}
                span.code {font-family: monospace; font-size: 12px; background-color: #CCC;}
            </style>
        </head>

        <body>
        ''']
    html_output.append("<p>Last update: " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "</p>")
    html_output.append("        <p>Analyzing product: Firefox</p>")
    html_output.append("        <p>Branch: " + clbranch + "</p>")

    if (clbranch=="all") or (clbranch=="release"):
        extract_p12n_channel(release_source, release_l10n, release_locales, "release", jsondata, html_output)
    if (clbranch=="all") or (clbranch=="beta"):
        extract_p12n_channel(beta_source, beta_l10n, beta_locales, "beta", jsondata, html_output)
    if (clbranch=="all") or (clbranch=="aurora"):
        extract_p12n_channel(aurora_source, aurora_l10n, aurora_locales, "aurora", jsondata, html_output)
    if (clbranch=="all") or (clbranch=="trunk"):
        extract_p12n_channel(trunk_source, trunk_l10n, trunk_locales, "trunk", jsondata, html_output)

    # Write back updated json data
    jsonfile = open(jsonfilename, "w")
    jsonfile.write(json.dumps(jsondata, indent=4, sort_keys=True))
    jsonfile.close()

    # Finalize and write html
    html_output.append("</body>")
    html_code = "\n".join(html_output)
    html_file = open(htmlfilename, "w")
    html_file.write(html_code)
    html_file.close()





if __name__ == "__main__":
    main()
