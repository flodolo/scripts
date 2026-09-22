#!/usr/bin/env python3
"""Dump the locale's existing translations as an aligned en-US/locale corpus.

This is the raw material for the style guide: reading a few hundred real
translations side by side is what reveals the team's conventions (formal vs
informal address, imperative vs infinitive for buttons, quotation marks,
whether UI terms are translated or kept in English, how placeholders are
positioned).

Output is TSV: resource <TAB> key <TAB> en-US <TAB> locale

Usage:
    dump_pairs.py LOCALE [--config firefox.toml] [--sample N] [--grep WORD]
"""

from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from l10nutil import entry_map, message_text, read, reference_pairs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("locale")
    ap.add_argument("--config", default="firefox.toml")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--sample", type=int, help="random sample of N pairs")
    ap.add_argument("--grep", help="only pairs whose en-US text contains this")
    ap.add_argument("--seed", type=int, default=0, help="sampling seed")
    ap.add_argument("--out", help="write here instead of stdout")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    rows = []
    for ref_path, target_path, resource in reference_pairs(
        repo, args.config, args.locale
    ):
        if not os.path.exists(target_path) or not os.path.exists(ref_path):
            continue
        reference = entry_map(read(ref_path))
        for entry in entry_map(read(target_path)).values():
            source = reference.get(entry.id)
            if source is None:
                continue
            en = message_text(source.value)
            text = message_text(entry.value)
            if not en or not text:
                continue
            if args.grep and args.grep.lower() not in en.lower():
                continue
            rows.append((resource, ".".join(entry.id), en, text))

    if args.sample and args.sample < len(rows):
        random.seed(args.seed)
        rows = random.sample(rows, args.sample)
    rows.sort()

    body = "".join("\t".join(r) + "\n" for r in rows)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"{len(rows)} pairs -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
