#!/usr/bin/env python3
"""Find the strings a locale has not translated yet, and stage them.

Every locale file here carries the same trans-unit set as
`en-US/firefox-ios.xliff`; a string is missing when its `<trans-unit>` has no
`<target>`. So unlike a multi-file project there is nothing to "add" -- the
gap is entirely untranslated units.

Writes a *staging tree* holding a partial XLIFF with only those units. The
pretranslation upload API is additive, so a partial file updates only the
strings it contains, and the repository's locale files -- which Pontoon's sync
owns -- are never touched.

If the locale has no directory yet (a locale newly enabled in Pontoon), the
staging file is built from the en-US reference with the locale's
`target-language`, so a brand-new locale backfills like any other.

Output under `<out>/<locale>/`:

    locale.json     locale metadata from Pontoon (direction, team description)
    manifest.json   {locale, project, files: [{file, resource, entries}]}
                    (`file` is relative to the manifest itself)
    report.md       human-readable summary
    staged/firefox-ios.xliff   partial XLIFF, targets still empty or English

Usage:
    analyze_locale.py LOCALE [--filter SUBSTRING] [--report-only]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from l10nutil import (  # noqa: E402
    NOT_PONTOON_LOCALES,
    entry_map,
    PROJECT_SLUG,
    RESOURCE_PATH,
    entity_key,
    entries,
    is_translated,
    locale_path,
    read,
    reference_path,
    subset,
    write_resource,
)

PONTOON = "https://pontoon.mozilla.org"


def fetch_locale_meta(locale: str) -> dict:
    url = f"{PONTOON}/api/v2/locales/{locale}/"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except Exception as exc:
        print(f"WARNING: could not fetch locale metadata: {exc}", file=sys.stderr)
        return {"code": locale, "offline": True}
    return {
        "code": data.get("code", locale),
        "name": data.get("name"),
        "direction": data.get("direction"),
        "script": data.get("script"),
        "cldr_plurals": data.get("cldr_plurals"),
        "plural_rule": data.get("plural_rule"),
        "team_description": data.get("team_description"),
    }


def retarget(res, locale: str):
    """Point a resource parsed from en-US at another locale.

    Only used when the locale has no file yet: the `<file target-language>`
    must name the locale, or Pontoon rejects the upload.
    """
    sections = []
    for section in res.sections:
        meta = [
            replace(m, value=locale) if m.key == "@target-language" else m
            for m in section.meta
        ]
        sections.append(replace(section, meta=meta))
    return replace(res, sections=sections)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("locale", help="Pontoon locale code, i.e. the directory name")
    ap.add_argument("--repo", default=".", help="path to the firefoxios-l10n checkout")
    ap.add_argument("--out", default=".backfill", help="staging root")
    ap.add_argument(
        "--filter", help="only units whose <file original> or id contains this"
    )
    ap.add_argument("--project", default=PROJECT_SLUG, help="Pontoon project slug")
    ap.add_argument(
        "--report-only", action="store_true", help="do not write the staging tree"
    )
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    locale = args.locale

    if locale in NOT_PONTOON_LOCALES:
        print(
            f"ERROR: '{locale}' is not a Pontoon locale for this project. "
            "en-US is the reference; es is generated from es-ES by update_es.yml.",
            file=sys.stderr,
        )
        return 2

    path = locale_path(repo, locale)
    new_locale = not os.path.exists(path)
    if new_locale:
        print(f"note: {locale}/ does not exist yet; staging from the en-US reference")
        res = retarget(read(reference_path(repo)), locale)
    else:
        res = read(path)

    meta = fetch_locale_meta(locale)

    missing, by_file = [], {}
    total = 0
    for section, entry in entries(res):
        total += 1
        if not new_locale and is_translated(entry):
            continue
        key = entity_key(section, entry)
        if args.filter and args.filter not in "/".join(key):
            continue
        missing.append(key)
        by_file[section.id[0]] = by_file.get(section.id[0], 0) + 1

    print(f"locale:    {locale} ({meta.get('name') or 'unknown'})")
    print(f"project:   {args.project}")
    print(f"resource:  {RESOURCE_PATH}")
    if new_locale:
        print("status:    NEW locale, no file in this repository yet")
    print(f"units:     {total} total, {len(missing)} untranslated")
    for original, count in sorted(by_file.items(), key=lambda kv: -kv[1]):
        print(f"  {count:>5}  {original}")

    if args.report_only or not missing:
        if not missing:
            print("\nnothing to backfill")
        return 0

    base = os.path.join(repo, args.out, locale)
    staged = os.path.join(base, "staged", RESOURCE_PATH)
    # Seed each staged target with the en-US text, so there is something to
    # overwrite and the placeholders start out correct.
    reference = entry_map(read(reference_path(repo)))
    write_resource(staged, subset(res, set(missing), seed=reference))

    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, "locale.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(base, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "locale": locale,
                "project": args.project,
                "files": [
                    {
                        "file": os.path.relpath(staged, base),
                        "resource": RESOURCE_PATH,
                        "entries": len(missing),
                        "new_locale": new_locale,
                    }
                ],
            },
            fh,
            indent=2,
            ensure_ascii=False,
        )
    with open(os.path.join(base, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# {locale} backfill\n\n")
        fh.write(f"- project: `{args.project}`, resource `{RESOURCE_PATH}`\n")
        fh.write(f"- {len(missing)} untranslated of {total} units\n")
        if new_locale:
            fh.write("- **new locale**: no file in this repository yet\n")
        fh.write("\n| units | `<file original>` |\n|--:|---|\n")
        for original, count in sorted(by_file.items(), key=lambda kv: -kv[1]):
            fh.write(f"| {count} | `{original}` |\n")

    print(f"\nstaged:   {os.path.relpath(staged, repo)}")
    print(f"manifest: {os.path.relpath(os.path.join(base, 'manifest.json'), repo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
