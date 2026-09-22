#! /usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Add missing <target> elements to a locale file.

Input is a JSON list of {"file": ..., "id": ..., "target": ...}. Existing
targets are never overwritten, and units absent from the reference locale
(obsolete strings) are never touched.
"""

import argparse
import json
import sys

from lxml import etree

from xliff_common import NS, index, locale_path, parse, units, write_xliff


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file with the new translations")
    parser.add_argument("--locale", default="en-CA")
    parser.add_argument("--reference", default="en-US")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(args.input) as fp:
        entries = json.load(fp)

    pending = {}
    for entry in entries:
        key = (entry["file"], entry["id"])
        if key in pending:
            sys.exit(f"ERROR: duplicate entry for {key}")
        if "target" not in entry:
            sys.exit(f"ERROR: entry without a target: {key}")
        pending[key] = entry["target"]

    reference = index(parse(args.reference))
    tree = parse(args.locale)

    added = 0
    skipped = []
    for original, unit in units(tree):
        key = (original, unit.get("id"))
        if key not in pending:
            continue
        target = pending.pop(key)
        if key not in reference:
            skipped.append(f"obsolete, not in {args.reference}: {key}")
            continue
        source = unit.find(f"{{{NS}}}source")
        if unit.find(f"{{{NS}}}target") is not None:
            skipped.append(f"already translated: {key}")
            continue
        node = etree.SubElement(unit, f"{{{NS}}}target")
        node.text = target
        # <target> belongs right after <source>, before <note>.
        source.addnext(node)
        added += 1

    for key in pending:
        skipped.append(f"no matching trans-unit: {key}")

    for message in skipped:
        print(f"SKIPPED: {message}")

    if args.dry_run:
        print(f"\nDry run: would add {added} targets, skip {len(skipped)}.")
        return

    write_xliff(tree.getroot(), locale_path(args.locale))
    print(f"\nAdded {added} targets to {args.locale}, skipped {len(skipped)}.")


if __name__ == "__main__":
    main()
