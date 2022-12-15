#!/usr/bin/env python3

"""
This script is used to read:
- All locales enabled for Firefox and firefox-for-android (Fenix) in Pontoon
- All locales shipping in Nightly and Release
- Locales supported in CLDR "full"
- Locales available but not included in CLDR "full"

Output data as CSV.
"""

import json
from urllib.parse import quote as urlquote
from urllib.request import urlopen


def main():
    locales = {
        "pontoon": [],
        "nightly": [],
        "release": [],
        "firefox-for-android": [],
        "cldr": [],
        "seed": [],
    }

    # Get the list of locales enabled in Pontoon.
    query = urlquote(
        """
{
  firefox: project(slug: "firefox") {
    localizations {
        locale {
            code
        }
    }
  }

  android: project(slug: "firefox-for-android") {
    localizations {
        locale {
            code
        }
    }
  }
}
"""
    )
    try:
        print("Reading Pontoon stats...")
        url = f"https://pontoon.mozilla.org/graphql?query={query}"
        response = urlopen(url)
        json_data = json.load(response)
        for project, project_data in json_data["data"].items():
            for element in project_data["localizations"]:
                locale = element["locale"]["code"]
                if project == "android":
                    locales["firefox-for-android"].append(locale)
                locales["pontoon"].append(locale)
    except Exception as e:
        print(e)
    # Remove duplicates and sort
    locales["pontoon"] = list(set(locales["pontoon"]))
    locales["pontoon"].sort()
    locales["firefox-for-android"].sort()

    # Get the list of locales enabled in Nightly
    try:
        print("Reading Nightly locales...")
        url = "https://hg.mozilla.org/mozilla-central/raw-file/tip/browser/locales/all-locales"
        with urlopen(url) as response:
            for locale in response:
                locales["nightly"].append(locale.rstrip().decode())
        locales["nightly"].sort()
    except Exception as e:
        print(e)

    # Get the list of locales enabled in Release
    try:
        print("Reading Release locales...")
        url = "https://hg.mozilla.org/mozilla-central/raw-file/tip/browser/locales/shipped-locales"
        with urlopen(url) as response:
            for locale in response:
                locales["release"].append(locale.rstrip().decode())
        locales["release"].sort()
    except Exception as e:
        print(e)

    # Create the superset of Mozilla locales
    mozilla_locales = []
    for group_locales in locales.values():
        mozilla_locales += group_locales
    mozilla_locales = list(set(mozilla_locales))
    mozilla_locales.sort()

    # Get the version of CLDR
    try:
        print("Reading CLDR version...")
        url = "https://api.github.com/repos/unicode-org/cldr-json/releases/latest"
        response = urlopen(url)
        json_data = json.load(response)
        cldr_version = json_data["tag_name"]
    except Exception as e:
        print(e)

    # Get the list of CLDR locales in 'full'
    try:
        print("Reading CLDR data...")
        url = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-core/availableLocales.json"
        response = urlopen(url)
        json_data = json.load(response)
        locales["cldr"] = json_data["availableLocales"]["full"]
    except Exception as e:
        print(e)

    # Try to figure out the list of seed locales in CLDR
    # Get the list of locales available in common/main, remove locales that
    # are actually supported
    url = "https://api.github.com/repos/unicode-org/cldr/contents/common/main/"
    try:
        print("Reading list of all locales in CLDR...")
        response = urlopen(url)
        json_data = json.load(response)
        all_locales = []
        for element in json_data:
            locale = element["name"].rstrip(".xml").replace("_", "-")
            all_locales.append(locale)
        # Remove locales available in supported, leaving out "seed" locales
        locales["seed"] = list(set(all_locales) - set(locales["cldr"]))
        locales["seed"].sort()
    except Exception as e:
        print(e)

    data = {}
    for locale in mozilla_locales:
        locale_no_region = locale.split("-")[0]
        if locale in locales["cldr"]:
            # Locale is available with the same code in CLDR
            cldr_status = "yes"
            cldr_notes = ""
        elif locale_no_region in locales["cldr"]:
            # Locale is available without the region code in CLDR
            # (e.g. 'ga-IE' in Mozilla, 'ga' in CLDR)
            cldr_status = "yes"
            cldr_notes = f"Available as {locale_no_region}"
        elif locale in locales["seed"]:
            # Locale is available with the same code in seed
            cldr_status = "seed"
            cldr_notes = ""
        elif locale_no_region in locales["seed"]:
            # Locale is available without the region code in seed
            # (e.g. 'ga-IE' in Mozilla, 'ga' in CLDR)
            cldr_status = "seed"
            cldr_notes = f"Available as {locale_no_region}"
        else:
            # Locale is not available at all
            cldr_status = "no"
            cldr_notes = ""

        data[locale] = {
            "pontoon": "yes" if locale in locales["pontoon"] else "no",
            "nightly": "yes" if locale in locales["nightly"] else "no",
            "release": "yes" if locale in locales["release"] else "no",
            "firefox-for-android": "yes"
            if locale in locales["firefox-for-android"]
            else "no",
            "cldr": cldr_status,
            "notes": cldr_notes,
        }

    output = []
    output.append(
        f"Locale Code,Pontoon,Firefox Nightly,Firefox Release,"
        f"firefox-for-android,CLDR ({cldr_version}),CLDR Notes"
    )
    for locale, locale_data in data.items():
        output.append(
            f"{locale},{locale_data['pontoon']},{locale_data['nightly']},"
            f"{locale_data['release']},{locale_data['firefox-for-android']},"
            f"{locale_data['cldr']},{locale_data['notes']}"
        )

    print("CSV OUTPUT\n\n")
    print("\n".join(output))


if __name__ == "__main__":
    main()
