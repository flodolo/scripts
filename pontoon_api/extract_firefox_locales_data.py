#!/usr/bin/env python3

import json
import os
import sys
from urllib.parse import quote as urlquote
from urllib.request import urlopen


def main():
    locales = [
        "ach",
        "af",
        "an",
        "ar",
        "ast",
        "az",
        "be",
        "bg",
        "bn",
        "br",
        "bs",
        "ca",
        "ca-valencia",
        "cak",
        "cs",
        "cy",
        "da",
        "de",
        "dsb",
        "el",
        "en-CA",
        "en-GB",
        "eo",
        "es-AR",
        "es-CL",
        "es-ES",
        "es-MX",
        "et",
        "eu",
        "fa",
        "ff",
        "fi",
        "fr",
        "fy-NL",
        "ga-IE",
        "gd",
        "gl",
        "gn",
        "gu-IN",
        "he",
        "hi-IN",
        "hr",
        "hsb",
        "hu",
        "hy-AM",
        "ia",
        "id",
        "is",
        "it",
        "ja",
        "ka",
        "kab",
        "kk",
        "km",
        "kn",
        "ko",
        "lij",
        "lt",
        "lv",
        "mk",
        "mr",
        "ms",
        "my",
        "nb-NO",
        "ne-NP",
        "nl",
        "nn-NO",
        "oc",
        "pa-IN",
        "pl",
        "pt-BR",
        "pt-PT",
        "rm",
        "ro",
        "ru",
        "si",
        "sk",
        "sl",
        "son",
        "sq",
        "sr",
        "sv-SE",
        "ta",
        "te",
        "th",
        "tl",
        "tr",
        "trs",
        "uk",
        "ur",
        "uz",
        "vi",
        "xh",
        "zh-CN",
        "zh-TW",
    ]

    # Get completion stats for locales from Pontoon
    query = """
{
    projects {
        name
        slug
        localizations {
            locale {
                code
            },
            missingStrings,
            unreviewedStrings,
            totalStrings
        }
    }
}
"""
    projects_list = {}
    locale_data = {}
    try:
        print("Reading Pontoon stats...")
        url = "https://pontoon.mozilla.org/graphql?query={}".format(urlquote(query))
        response = urlopen(url)
        json_data = json.load(response)

        for project in json_data["data"]["projects"]:
            slug = project["slug"]
            if slug in ["pontoon-intro", "tutorial"]:
                continue
            if not slug in projects_list:
                projects_list[slug] = project["name"]

            for element in project["localizations"]:
                locale = element["locale"]["code"]
                if not locale in locale_data:
                    locale_data[locale] = {
                        "stats": {
                            "missing": 0,
                            "unreviewed": 0,
                            "projects": 0,
                        },
                    }
                locale_data[locale][slug] = {
                    "missing": element["missingStrings"],
                    "unreviewed": element["unreviewedStrings"],
                }
                locale_data[locale]["stats"]["projects"] += 1
                locale_data[locale]["stats"]["missing"] += element["missingStrings"]
                locale_data[locale]["stats"]["unreviewed"] += element[
                    "unreviewedStrings"
                ]
    except Exception as e:
        print(e)

    output = []
    output.append(
        "Locale,Number of Projects,Projects,Missing Strings,Pending Suggestions,Latest Activity"
    )
    # Only print requested locales
    for locale in locales:
        if not locale in locale_data:
            print("ERROR: no data available for {}".format(locale))
        data = locale_data[locale]["stats"]

        # Get the list of projects
        project_slugs = list(locale_data[locale].keys())
        project_slugs.remove("stats")
        project_slugs.sort()
        output.append(
            "{},{},{},{},{},".format(
                locale,
                data["projects"],
                " ".join(project_slugs),
                data["missing"],
                data["unreviewed"],
            )
        )

    # Save locally
    with open("output.csv", "w") as f:
        f.write("\n".join(output))
        print("Data stored as output.csv")


if __name__ == "__main__":
    main()
