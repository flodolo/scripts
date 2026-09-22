#!/usr/bin/env python3
"""Download Pontoon's terminology for a locale and flatten it to TSV.

The raw TBX is verbose XML; this prints one line per concept so the whole
glossary can be read in one pass:

    en_term <TAB> locale_term <TAB> part of speech <TAB> definition

Concepts with no translation for the locale are skipped unless --all is given.

Usage:
    fetch_terminology.py LOCALE [--out FILE] [--all]
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from xml.etree import ElementTree as ET

TBX_URL = "https://pontoon.mozilla.org/terminology/{locale}.tbx"
NS = {"t": "urn:iso:std:iso:30042:ed-2"}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def flatten(tbx: bytes, locale: str, keep_untranslated: bool):
    root = ET.fromstring(tbx)
    for concept in root.iter(f"{{{NS['t']}}}conceptEntry"):
        source = target = pos = definition = ""
        for sec in concept.findall("t:langSec", NS):
            lang = sec.get(XML_LANG, "")
            term_sec = sec.find("t:termSec", NS)
            if term_sec is None:
                continue
            term = (term_sec.findtext("t:term", "", NS) or "").strip()
            if lang.startswith("en"):
                source = term
                note = term_sec.find('t:termNote[@type="partOfSpeech"]', NS)
                pos = (note.text or "").strip() if note is not None else ""
                d = term_sec.find('.//t:descrip[@type="definition"]', NS)
                definition = " ".join((d.text or "").split()) if d is not None else ""
            elif lang == locale:
                target = term
        if not source:
            continue
        if not target and not keep_untranslated:
            continue
        yield source, target, pos, definition


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("locale", help="Pontoon locale code, e.g. 'it'")
    ap.add_argument("--out", help="write here instead of stdout")
    ap.add_argument(
        "--all", action="store_true", help="include concepts with no translation"
    )
    args = ap.parse_args()

    url = TBX_URL.format(locale=args.locale)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            tbx = resp.read()
    except Exception as exc:
        print(f"ERROR: could not download {url}: {exc}", file=sys.stderr)
        return 1

    rows = list(flatten(tbx, args.locale, args.all))
    lines = ["\t".join(r) for r in sorted(rows, key=lambda r: r[0].lower())]
    body = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"{len(rows)} terms -> {args.out}")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
