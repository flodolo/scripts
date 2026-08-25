#! /usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""List trans-units in a locale that have no <target> yet."""

import argparse
import json

from xliff_common import index, parse, text_of, units


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale", default="en-CA")
    parser.add_argument("--reference", default="en-US")
    parser.add_argument("--output", default="/tmp/en-CA-missing.json")
    args = parser.parse_args()

    reference = index(parse(args.reference))
    tree = parse(args.locale)

    missing = []
    obsolete = []
    translated = 0
    for original, unit in units(tree):
        key = (original, unit.get("id"))
        if key not in reference:
            obsolete.append(key)
            continue
        if unit.find("{urn:oasis:names:tc:xliff:document:1.2}target") is not None:
            translated += 1
            continue
        missing.append(
            {
                "file": original,
                "id": unit.get("id"),
                "source": text_of(unit, "source"),
                "note": text_of(unit, "note"),
            }
        )

    with open(args.output, "w") as fp:
        json.dump(missing, fp, indent=2, ensure_ascii=False)

    print(f"{args.locale}: {translated} translated, {len(missing)} missing")
    print(f"obsolete (absent from {args.reference}, leave untouched): {len(obsolete)}")
    for original, unit_id in obsolete:
        print(f"  {original}:{unit_id}")
    print(f"\nWrote {len(missing)} entries to {args.output}")


if __name__ == "__main__":
    main()
