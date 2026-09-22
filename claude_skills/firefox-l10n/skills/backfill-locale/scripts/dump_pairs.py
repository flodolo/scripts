#!/usr/bin/env python3
"""Dump the locale's existing translations as an aligned en-US/locale corpus.

This is the raw material for the style guide: reading a few hundred real
translations side by side is what reveals the team's conventions (formal vs
informal address, imperative vs infinitive for buttons, quotation marks,
whether UI terms are translated or kept in English, how `%@` is positioned).

XLIFF keeps the English `<source>` next to every `<target>`, so no reference
lookup is needed.

Output is TSV: file original <TAB> unit id <TAB> en-US <TAB> locale

Usage:
    dump_pairs.py LOCALE [--sample N] [--grep WORD] [--out FILE]
"""

from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from l10nutil import (  # noqa: E402
    entries,
    is_translated,
    locale_path,
    message_text,
    read,
    source_text,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("locale")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--sample", type=int, help="random sample of N pairs")
    ap.add_argument("--grep", help="only pairs whose en-US text contains this")
    ap.add_argument("--seed", type=int, default=0, help="sampling seed")
    ap.add_argument("--out", help="write here instead of stdout")
    args = ap.parse_args()

    path = locale_path(os.path.abspath(args.repo), args.locale)
    if not os.path.exists(path):
        print(f"ERROR: no file for '{args.locale}' at {path}", file=sys.stderr)
        return 2

    rows = []
    for section, entry in entries(read(path)):
        if not is_translated(entry):
            continue
        en = source_text(entry)
        text = message_text(entry.value)
        if not en or not text:
            continue
        if args.grep and args.grep.lower() not in en.lower():
            continue
        rows.append((section.id[0], entry.id[0], en, text))

    if args.sample and args.sample < len(rows):
        random.seed(args.seed)
        rows = random.sample(rows, args.sample)
    rows.sort()

    body = "".join("\t".join(r).replace("\n", "\\n") + "\n" for r in rows)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"{len(rows)} pairs -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
