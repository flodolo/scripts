#!/usr/bin/env python3
"""Check a staged backfill before it is uploaded as pretranslations.

Every problem reported here would either be rejected by Pontoon's quality
checks or, worse, silently published as a bad pretranslation.

Checks run against the parsed `moz.l10n` model rather than the raw text, so
placeholders are compared as structured data and an escaping mistake shows up
as a parse or normalization difference instead of a regex guess:

  xml            the staged file does not parse as Android XML
  unknown-key    the entry is not in the reference (nothing to upload it to)
  placeholder    a placeholder was dropped, added or renumbered
  plural         the plural categories do not match the locale's CLDR set
  normalization  re-serializing the file does not reproduce it, which means an
                 escape is wrong -- an unescaped `"` in particular is silently
                 swallowed by Android and would lose text
  untranslated   the value is still identical to the en-US reference

`untranslated` is a warning, not an error: some strings legitimately stay in
English (brand names, "OK"). Review each one and pass --allow-untranslated
once you have. Everything else is an error and blocks the upload.

Usage:
    verify_staged.py --manifest .backfill/LOCALE/manifest.json [--repo .]
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moz.l10n.resource import serialize_resource  # noqa: E402

from l10nutil import (  # noqa: E402
    entries,
    entry_map,
    message_text,
    placeholders_by_variant,
    plural_categories,
    read,
    variant_categories,
)


def check_file(repo, staged_path, resource, categories, allow_untranslated):
    issues = []

    def add(kind, key, detail):
        issues.append((kind, resource, key, detail))

    try:
        staged = read(staged_path)
    except Exception as exc:
        add("xml", "-", f"{type(exc).__name__}: {exc}")
        return issues

    # A faithful round-trip is the norm for these files, so any difference
    # means the hand-edited text is not what Android would actually read.
    with open(staged_path, encoding="utf-8") as fh:
        written = fh.read()
    canonical = "".join(serialize_resource(staged))
    if canonical != written:
        for line in difflib.unified_diff(
            written.splitlines(), canonical.splitlines(), "written", "parsed", n=0
        ):
            if line.startswith(("-", "+")) and not line.startswith(("---", "+++")):
                add("normalization", line[0], line[1:].strip()[:100])

    reference = entry_map(read(os.path.join(repo, resource)))
    for entry in entries(staged):
        ref = reference.get(entry.id)
        key = ".".join(entry.id)
        if ref is None:
            add("unknown-key", key, "not present in the en-US reference")
            continue

        got = variant_categories(entry.value)
        if got and got != categories:
            add("plural", key, f"{got} != expected {categories}")

        # Compare each plural form against the matching reference form, or
        # against the reference catch-all when the locale has a category
        # English does not.
        ref_ph = placeholders_by_variant(ref.value)
        ref_default = ref_ph.get("other") or list(ref_ph.values())[-1]
        for category, actual_ph in placeholders_by_variant(entry.value).items():
            expected_ph = ref_ph.get(category, ref_default)
            if expected_ph != actual_ph:
                label = f"{key}[{category}]" if category else key
                add("placeholder", label, f"expected {expected_ph}, got {actual_ph}")

        text = message_text(entry.value)
        if not text.strip():
            add("untranslated", key, "empty value")
        elif not allow_untranslated and text == message_text(ref.value):
            add("untranslated", key, f"still en-US: {text[:60]!r}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="path to manifest.json")
    ap.add_argument("--repo", default=".", help="path to the android-l10n checkout")
    ap.add_argument(
        "--allow-untranslated",
        action="store_true",
        help="stop reporting values identical to en-US (only after reviewing them)",
    )
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    manifest_path = os.path.abspath(args.manifest)
    base = os.path.dirname(manifest_path)
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    cldr = "1,5"
    locale_meta_path = os.path.join(base, "locale.json")
    if os.path.exists(locale_meta_path):
        with open(locale_meta_path, encoding="utf-8") as fh:
            cldr = json.load(fh).get("cldr_plurals", "1,5")
    categories = plural_categories(cldr)

    all_issues = []
    for entry in manifest["files"]:
        all_issues += check_file(
            repo,
            os.path.join(base, entry["file"]),
            entry["resource"],
            categories,
            args.allow_untranslated,
        )

    counts: dict[str, int] = {}
    for kind, resource, key, detail in all_issues:
        counts[kind] = counts.get(kind, 0) + 1
        print(f"{kind:<14} {resource}\n               {key}: {detail}")

    blocking = sum(v for k, v in counts.items() if k != "untranslated")
    print("\n--- summary ---")
    for kind, count in sorted(counts.items()):
        print(f"{kind:<14} {count}")
    if not counts:
        print("clean")
    print(f"\nblocking issues: {blocking}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
