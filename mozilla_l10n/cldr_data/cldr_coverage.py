#!/usr/bin/env python3

"""
This script is used to read:
- All locales enabled for Firefox and firefox-for-android (Fenix) in Pontoon
- All locales shipping in Nightly and Release
- Locales supported in CLDR "full"
- Locales available but not included in CLDR "full"

Output data as CSV.
"""

import requests
import sys


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
    url = "https://pontoon.mozilla.org/api/v2/projects"
    page = 1
    try:
        while url:
            print(f"Reading projects (page {page})")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for project in data.get("results", {}):
                slug = project["slug"]
                if slug in ["firefox-for-android", "firefox"]:
                    if slug == "firefox-for-android":
                        locales["firefox-for-android"] = sorted(project["locales"])
                    locales["pontoon"].extend(project["locales"])

            # Get the next page URL
            url = data.get("next")
            page += 1
        # Remove duplicates and sort
        locales["pontoon"] = list(set(locales["pontoon"]))
        locales["pontoon"].sort()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit()

    # Get the list of locales enabled in Nightly
    try:
        print("Reading Nightly locales...")
        url = "https://raw.githubusercontent.com/mozilla-firefox/firefox/refs/heads/main/browser/locales/all-locales"
        response = requests.get(url)
        response.raise_for_status()
        for locale in response.iter_lines():
            locales["nightly"].append(locale.rstrip().decode())
        locales["nightly"].sort()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

    # Get the list of locales enabled in Release
    try:
        print("Reading Release locales...")
        url = "https://raw.githubusercontent.com/mozilla-firefox/firefox/refs/heads/main/browser/locales/shipped-locales"
        response = requests.get(url)
        response.raise_for_status()
        for locale in response.iter_lines():
            locales["release"].append(locale.rstrip().decode())
        locales["release"].sort()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

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
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()
        cldr_version = json_data["tag_name"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

    # Get the list of CLDR locales in 'full'
    try:
        print("Reading CLDR data...")
        url = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-core/availableLocales.json"
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()
        locales["cldr"] = json_data["availableLocales"]["full"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

    # Try to figure out the list of seed locales in CLDR
    # Get the list of locales available in common/main, remove locales that
    # are actually supported
    url = "https://api.github.com/repos/unicode-org/cldr/contents/common/main/"
    try:
        print("Reading list of all locales in CLDR...")
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()
        all_locales = []
        for element in json_data:
            locale = element["name"].rstrip(".xml").replace("_", "-")
            all_locales.append(locale)
        # Remove locales available in supported, leaving out "seed" locales
        locales["seed"] = list(set(all_locales) - set(locales["cldr"]))
        locales["seed"].sort()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")

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
