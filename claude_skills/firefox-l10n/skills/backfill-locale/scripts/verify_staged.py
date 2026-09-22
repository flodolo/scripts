#!/usr/bin/env python3
"""Check a staged backfill before it is uploaded as pretranslations.

Checks run against the parsed `moz.l10n` model rather than the raw text, so
iOS format specifiers are compared as structured data:

  xml            the staged file does not parse as XLIFF
  unknown-key    the unit is not in the en-US reference
  missing-target the unit has no `<target>` at all, so it would upload nothing
  placeholder    a format specifier was dropped, added or renumbered
  normalization  re-serializing does not reproduce the file, which means the
                 hand-edited XML is not what Pontoon would read
  untranslated   the target is still identical to the en-US source

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
    entity_key,
    entries,
    entry_map,
    is_translated,
    message_text,
    placeholders,
    read,
    reference_path,
    source_text,
)


def check_file(repo, staged_path, allow_untranslated):
    issues = []

    def add(kind, key, detail):
        issues.append((kind, key, detail))

    try:
        staged = read(staged_path)
    except Exception as exc:
        add("xml", "-", f"{type(exc).__name__}: {exc}")
        return issues

    # A faithful round-trip is the norm for these files, so any difference
    # means the hand-edited text is not what the parser actually sees.
    with open(staged_path, encoding="utf-8") as fh:
        written = fh.read()
    canonical = "".join(serialize_resource(staged))
    if canonical != written:
        for line in difflib.unified_diff(
            written.splitlines(), canonical.splitlines(), "written", "parsed", n=0
        ):
            if line.startswith(("-", "+")) and not line.startswith(("---", "+++")):
                # repr, so a whitespace-only difference is actually visible
                add("normalization", line[0], repr(line[1:])[:110])

    reference = entry_map(read(reference_path(repo)))
    for section, entry in entries(staged):
        key = entity_key(section, entry)
        label = " / ".join(key)
        ref = reference.get(key)
        if ref is None:
            add("unknown-key", label, "not present in the en-US reference")
            continue

        if not is_translated(entry):
            add("missing-target", label, "no <target>; it would upload nothing")
            continue

        expected = placeholders(ref.value)
        actual = placeholders(entry.value)
        if expected != actual:
            add("placeholder", label, f"expected {expected}, got {actual}")

        text = message_text(entry.value)
        if not text.strip():
            add("untranslated", label, "empty target")
        elif not allow_untranslated and text == source_text(entry):
            add("untranslated", label, f"still en-US: {text[:60]!r}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="path to manifest.json")
    ap.add_argument("--repo", default=".", help="path to the firefoxios-l10n checkout")
    ap.add_argument(
        "--allow-untranslated",
        action="store_true",
        help="stop reporting targets identical to en-US (only after reviewing them)",
    )
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    manifest_path = os.path.abspath(args.manifest)
    base = os.path.dirname(manifest_path)
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    all_issues = []
    for entry in manifest["files"]:
        all_issues += check_file(
            repo, os.path.join(base, entry["file"]), args.allow_untranslated
        )

    counts: dict[str, int] = {}
    for kind, key, detail in all_issues:
        counts[kind] = counts.get(kind, 0) + 1
        print(f"{kind:<14} {key}\n               {detail}")

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
