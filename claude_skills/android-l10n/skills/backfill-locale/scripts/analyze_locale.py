#!/usr/bin/env python3
"""Find what a locale is missing against the en-US reference, and stage it.

Compares every reference `values/strings.xml` listed in a project's l10n.toml
against the locale's `values-<android_locale>/strings.xml`, then writes a
*staging tree* containing only the missing entries. The staged files are
partial `strings.xml` files: the pretranslation upload API is additive, so a
partial file updates only the strings it contains.

The repository's locale files are written by Pontoon's sync and are never
touched by this skill; translations flow back through the API instead.

Parsing and serialization go through `moz.l10n`, so the staged files carry the
reference's comments, attributes and header verbatim.

Output under `<out>/<locale>/`:

    locale.json     locale metadata from Pontoon (plural categories, direction)
    manifest.json   [{file, resource, entries, new_file}] for the upload script
                    (`file` is relative to the manifest itself)
    report.md       human-readable summary
    staged/<resource path>   partial strings.xml, values still in English

Usage:
    analyze_locale.py LOCALE [--config firefox.toml] [--filter SUBSTRING]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moz.l10n.model import CatchallKey, Entry, SelectMessage  # noqa: E402

from l10nutil import (  # noqa: E402
    build_resource,
    entries,
    entry_map,
    plural_categories,
    project_slug,
    read,
    reference_pairs,
    write_resource,
)

PONTOON = "https://pontoon.mozilla.org"


def fetch_locale_meta(locale: str) -> dict:
    """Read plural categories, direction and team info from Pontoon."""
    url = f"{PONTOON}/api/v2/locales/{locale}/"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except Exception as exc:  # network is optional, fall back to en-like plurals
        print(f"WARNING: could not fetch locale metadata: {exc}", file=sys.stderr)
        return {"code": locale, "cldr_plurals": "1,5", "offline": True}
    return {
        "code": data.get("code", locale),
        "name": data.get("name"),
        "direction": data.get("direction"),
        "script": data.get("script"),
        "cldr_plurals": data.get("cldr_plurals", "1,5"),
        "plural_rule": data.get("plural_rule"),
        "plural_categories": plural_categories(data.get("cldr_plurals", "1,5")),
        "team_description": data.get("team_description"),
    }


def retarget_plurals(entry: Entry, categories: list[str]) -> Entry:
    """Give a plural entry the target locale's CLDR categories.

    English has only `one` and `other`. A locale with `few`/`many` needs a
    variant per category, so each missing one is seeded with the English
    catch-all pattern for the model to rewrite.
    """
    msg = entry.value
    if not isinstance(msg, SelectMessage):
        return entry

    by_category = {}
    catchall = None
    for key, pattern in msg.variants.items():
        name = key[0]
        if isinstance(name, CatchallKey):
            catchall = pattern
            by_category[name.value or "other"] = pattern
        else:
            by_category[str(name)] = pattern
    if catchall is None:
        catchall = next(iter(msg.variants.values()))

    variants = {}
    for category in categories:
        pattern = list(by_category.get(category, catchall))
        key = (CatchallKey(category),) if category == categories[-1] else (category,)
        variants[key] = pattern
    return replace(entry, value=replace(msg, variants=variants))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("locale", help="Pontoon locale code, e.g. 'it' or 'en-CA'")
    ap.add_argument("--config", default="firefox.toml", help="project l10n.toml")
    ap.add_argument("--repo", default=".", help="path to the android-l10n checkout")
    ap.add_argument("--out", default=".backfill", help="staging root")
    ap.add_argument("--filter", help="only resources whose path contains this")
    ap.add_argument("--project", help="Pontoon project slug (inferred from --config)")
    ap.add_argument(
        "--report-only", action="store_true", help="do not write the staging tree"
    )
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    project = args.project or project_slug(args.config)
    meta = fetch_locale_meta(args.locale)
    categories = meta.get("plural_categories") or plural_categories(
        meta.get("cldr_plurals", "1,5")
    )

    base = os.path.join(repo, args.out, args.locale)
    staged_root = os.path.join(base, "staged")

    manifest, rows = [], []
    total_missing = total_new_files = 0
    for ref_path, target_path, resource in sorted(
        reference_pairs(repo, args.config, args.locale), key=lambda p: p[2]
    ):
        if args.filter and args.filter not in resource:
            continue
        if not os.path.exists(ref_path):
            print(f"WARNING: missing reference {resource}", file=sys.stderr)
            continue

        reference = read(ref_path)
        new_file = not os.path.exists(target_path)
        present = set() if new_file else entry_map(read(target_path)).keys()
        missing = [e for e in entries(reference) if e.id not in present]
        if not missing:
            continue

        missing = [retarget_plurals(e, categories) for e in missing]
        total_missing += len(missing)
        total_new_files += int(new_file)
        rows.append((resource, len(missing), new_file))

        if not args.report_only:
            path = os.path.join(staged_root, resource)
            write_resource(path, build_resource(reference, missing))
            manifest.append(
                {
                    "file": os.path.relpath(path, base),
                    "resource": resource,
                    "entries": len(missing),
                    "new_file": new_file,
                }
            )

    print(f"locale:   {args.locale} ({meta.get('name') or 'unknown'})")
    print(f"project:  {project}")
    print(f"plurals:  {', '.join(categories)}")
    print(f"missing:  {total_missing} entries in {len(rows)} files")
    print(f"new files:{total_new_files:>4} (locale has no file at all)")
    for resource, count, new_file in rows:
        print(f"  {'NEW ' if new_file else '    '}{count:>5}  {resource}")

    if args.report_only:
        return 0

    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, "locale.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(base, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {"locale": args.locale, "project": project, "files": manifest},
            fh,
            indent=2,
            ensure_ascii=False,
        )
    with open(os.path.join(base, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# {args.locale} backfill\n\n")
        fh.write(f"- project: `{project}`\n")
        fh.write(f"- plural categories: {', '.join(categories)}\n")
        fh.write(f"- missing entries: {total_missing} across {len(rows)} files\n")
        fh.write(f"- files absent for this locale: {total_new_files}\n\n")
        fh.write("| entries | new file | resource |\n|--:|:-:|---|\n")
        for resource, count, new_file in rows:
            fh.write(f"| {count} | {'yes' if new_file else ''} | `{resource}` |\n")

    print(f"\nstaged under {os.path.relpath(staged_root, repo)}")
    print(f"manifest:    {os.path.relpath(os.path.join(base, 'manifest.json'), repo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
