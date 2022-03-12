#!/usr/bin/env python3

"""
This script is used to validate locale changes to l10n-changesets.json before
uplift to mozilla-release:
- It downloads the current mozilla-release file
- Identify differences
- Validate that the changesets actually exist in the corresponding l10n-central
  repositories
"""

import argparse
import json
import os
import sys
from urllib.request import urlopen


def main():
    p = argparse.ArgumentParser(
        description="Validate local changes to l10n-changesets.json"
    )

    p.add_argument("local_json", help="Path of local clone of mozilla-unified")
    args = p.parse_args()

    json_path = os.path.join(
        args.local_json, "browser", "locales", "l10n-changesets.json"
    )

    if not os.path.exists(json_path):
        sys.exit(f"File {json_path} does not exist.")

    with open(json_path) as f:
        local_json = json.load(f)

    try:
        print("Reading remote release JSON...")
        url = "https://hg.mozilla.org/releases/mozilla-release/raw-file/default/browser/locales/l10n-changesets.json"
        response = urlopen(url)
        remote_json = json.load(response)
    except Exception as e:
        print(e)

    errors = []
    warnings = []
    changes = {}
    for locale, locale_data in local_json.items():
        if not locale in remote_json:
            errors.append(f"{locale} not available in remote JSON.")

        if locale_data["revision"] != remote_json[locale]["revision"]:
            changes[locale] = locale_data["revision"]

    # Verify that the new changesets exist and warn if it's not the current tip
    print("Checking changesets for changed locales...")
    for locale, rev in changes.items():
        try:
            url = f"https://hg.mozilla.org/l10n-central/{locale}/json-pushes"
            response = urlopen(url)
            rev_json = json.load(response)

            rev_ok = False
            for id, data in rev_json.items():
                if rev in data["changesets"]:
                    rev_ok = True
            if not rev_ok:
                errors.append(f"{locale}: {rev} not available in changesets.")

            current_tip = rev_json[max(rev_json.keys())]["changesets"][0]
            if rev_ok and current_tip != rev:
                warnings.append(
                    f"{locale}: {rev} is not the current tip. Current tip: {current_tip}"
                )
        except Exception as e:
            print(e)

    if changes:
        print("\nChanged locales: " + ", ".join(changes.keys()))

    if errors:
        print("\n\n*** ERRORS ***")
        print("\n".join(errors))

    if warnings:
        print("\n\n*** WARNINGS ***")
        print("\n".join(warnings))


if __name__ == "__main__":
    main()
