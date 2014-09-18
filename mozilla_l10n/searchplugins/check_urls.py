#! /usr/bin/env python

import json
import urllib2

def main():
    json_file = open("searchplugins.json")
    json_data = json.load(json_file)

    # Ignore metadata, images and en-US
    del json_data["images"]
    del json_data["creation_date"]
    del json_data["en-US"]

    locales = []
    for locale in json_data:
        locales.append(locale)
    locales.sort()

    output_results = []
    for locale in locales:
        output_results.append(locale)
        for product in ["browser", "mobile"]:
            if product in json_data[locale]:
                output_results.append("** %s **" % (product))
                for element in json_data[locale][product]["aurora"]:
                    if (element != "p12n" and
                        "en-US" not in json_data[locale][product]["aurora"][element]["description"]):
                        # Ignore p12n and non localized searchplugins
                        sp = json_data[locale][product]["aurora"][element]
                        url_request = sp["url"]
                        print "Checking %s %s" % (locale, sp["file"])
                        try:
                            response = urllib2.urlopen(url_request.encode("utf8"))
                            result = response.code
                        except urllib2.HTTPError, e:
                            result = "ERROR (%s)" % (e.code)
                            result = unicode(result, "utf-8")
                        except urllib2.URLError, e:
                            result = "ERROR (%s)" % (e.args)
                            result = unicode(result, "utf-8")
                        output_results.append("%s: %s" % (sp["file"], result))

    f = open("results.txt", "w")
    f.write("\n".join(output_results).encode("utf8"))
    f.close()


if __name__ == "__main__":
    main()
