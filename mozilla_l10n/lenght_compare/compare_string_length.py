#! /usr/bin/env python

""" This script assumes that mozilla-beta localizations are stored in a
structure like the following:

this_script
    |__locales
        |__locale_code
            |__mozilla-aurora

I use this script to generate the full folder structure (all locales,
central+aurora+trunk):
https://github.com/flodolo/scripts/blob/master/mozilla_l10n/clone.sh

I use en-GB as a reference (suboptimal but practical, no point in cloning the
entire mozilla-* repository for strings). """

import os
import json
import sys
import subprocess
import re

# Import Silme library (http://hg.mozilla.org/l10n/silme/)
silmepath = os.path.join(os.getcwd(), "libraries", "silme")

if not os.path.isdir(silmepath):
    try:
        print "Cloning silme..."
        cmd_status = subprocess.check_output(
            "hg clone http://hg.mozilla.org/l10n/silme libraries/silme -u silme-0.8.0",
            stderr=subprocess.STDOUT,
            shell=True,
        )
        print cmd_status
    except Exception as e:
        print e

sys.path.append(os.path.join(silmepath, "lib"))
import silme.diff
import silme.core
import silme.format
import silme.io

silme.format.Manager.register("dtd", "properties")


def get_string(package, localdirectory, strings):
    for item in package:
        if (type(item[1]) is not silme.core.structure.Blob) and not (
            isinstance(item[1], silme.core.Package)
        ):
            for entity in item[1]:
                strings[localdirectory + "/" + item[0] + ":" + entity] = item[1][
                    entity
                ].get_value()
        elif isinstance(item[1], silme.core.Package):
            get_string(item[1], localdirectory + "/" + item[0], strings)


def main():
    locales_folder = os.path.join(os.getcwd(), "locales")
    repo_english = os.path.join(locales_folder, "en-GB", "mozilla-beta") + os.sep

    # Array to store statistics
    # global: count (number of strings), avg_chars (average difference in characters), avg_perc (average difference in %)
    # short (2<length<6)
    # middle (6<length<11)
    # long (11<length<21)
    # sentence length >20
    stats = {}

    for locale in sorted(os.listdir(locales_folder)):
        if not locale.startswith("."):
            stats[locale] = {
                "global": {
                    "count": 0,
                    "avg_chars": 0,
                    "avg_perc": 0,
                    "max_diff": 0,
                    "min_diff": 0,
                    "max_diff_id": "",
                    "min_diff_id": "",
                },
                "short": {
                    "count": 0,
                    "avg_chars": 0,
                    "avg_perc": 0,
                    "max_diff": 0,
                    "min_diff": 0,
                    "max_diff_id": "",
                    "min_diff_id": "",
                },
                "middle": {
                    "count": 0,
                    "avg_chars": 0,
                    "avg_perc": 0,
                    "max_diff": 0,
                    "min_diff": 0,
                    "max_diff_id": "",
                    "min_diff_id": "",
                },
                "long": {
                    "count": 0,
                    "avg_chars": 0,
                    "avg_perc": 0,
                    "max_diff": 0,
                    "min_diff": 0,
                    "max_diff_id": "",
                    "min_diff_id": "",
                },
                "sentence": {
                    "count": 0,
                    "avg_chars": 0,
                    "avg_perc": 0,
                    "max_diff": 0,
                    "min_diff": 0,
                    "max_diff_id": "",
                    "min_diff_id": "",
                },
            }
            print "Analyzing " + locale

            repo_locale = os.path.join(locales_folder, locale, "mozilla-beta") + os.sep
            directories = [
                "browser",
                "dom",
                "mail",
                "mobile",
                "netwerk",
                "security",
                "services",
                "suite",
                "toolkit",
                "webapprt",
            ]

            string_english = {}
            string_locale = {}

            for directory in directories:
                if os.path.isdir(os.path.join(repo_locale, directory)):
                    # Not all locales have all products localized, so missing folders that could stop the script
                    rcs_client_english = silme.io.Manager.get("file")
                    l10n_package_english = rcs_client_english.get_package(
                        repo_english + directory, object_type="entitylist"
                    )

                    rcs_client_locale = silme.io.Manager.get("file")
                    l10n_package_locale = rcs_client_locale.get_package(
                        repo_locale + directory, object_type="entitylist"
                    )

                    get_string(l10n_package_english, directory, string_english)
                    get_string(l10n_package_locale, directory, string_locale)

            for entity in string_locale:
                try:
                    try:
                        original = string_english[entity]
                        translation = string_locale[entity]
                    except Exception as e:
                        # print e
                        pass

                    if len(original) > 1:
                        # Ignore accesskeys or shortcuts
                        difference = len(translation) - len(original)
                        perc_difference = 100 * (difference / float(len(original)))

                        # General stats
                        stats[locale]["global"]["count"] += 1
                        stats[locale]["global"]["avg_chars"] += difference
                        stats[locale]["global"]["avg_perc"] += perc_difference

                        # Specific bucket stats
                        if len(original) < 6:
                            bucket = "short"
                        elif len(original) < 11:
                            bucket = "middle"
                        elif len(original) < 21:
                            bucket = "long"
                        else:
                            bucket = "sentence"
                        stats[locale][bucket]["count"] += 1
                        stats[locale][bucket]["avg_chars"] += difference
                        stats[locale][bucket]["avg_perc"] += perc_difference

                        # Store max_diff and min_diff for specific bucket
                        if difference > stats[locale][bucket]["max_diff"]:
                            stats[locale][bucket]["max_diff"] = difference
                            stats[locale][bucket]["max_diff_id"] = entity
                        if difference < stats[locale][bucket]["min_diff"]:
                            stats[locale][bucket]["min_diff"] = difference
                            stats[locale][bucket]["min_diff_id"] = entity

                        # Store max_diff and min_diff for global
                        if difference > stats[locale]["global"]["max_diff"]:
                            stats[locale]["global"]["max_diff"] = difference
                            stats[locale]["global"]["max_diff_id"] = entity
                        if difference < stats[locale]["global"]["min_diff"]:
                            stats[locale]["global"]["min_diff"] = difference
                            stats[locale]["global"]["min_diff_id"] = entity

                except Exception as e:
                    print e
                    pass

            # Calculate averages for all buckets
            for bucket in stats[locale]:
                if stats[locale][bucket]["count"] > 0:
                    stats[locale][bucket]["avg_chars"] = round(
                        float(stats[locale][bucket]["avg_chars"])
                        / stats[locale][bucket]["count"],
                        4,
                    )
                    stats[locale][bucket]["avg_perc"] = round(
                        float(stats[locale][bucket]["avg_perc"])
                        / stats[locale][bucket]["count"],
                        4,
                    )

    # Analysis completed, write down json
    jsonfile = open("stats.json", "w")
    jsonfile.write(json.dumps(stats, indent=4, sort_keys=True))
    jsonfile.close()


if __name__ == "__main__":
    main()
