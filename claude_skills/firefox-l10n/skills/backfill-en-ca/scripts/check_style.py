#!/usr/bin/env python3
"""Check en-CA strings against the en-CA style rules.

Run it after a backfill (or on any set of files) to catch en-US spellings,
straight apostrophes, double spaces, broken access keys, and placeholders that
do not match the en-US source.

Requires moz.l10n, so run it with the quarantine venv:

    ~/mozilla-source/git/firefox-quarantine/.venv/bin/python check_style.py [paths...]

Paths are files or directories, relative to the repo or absolute; with no
paths the whole en-CA tree is checked.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_adapt import adapt_text  # noqa: E402

from moz.l10n.model import CatchallKey, Expression, Markup, PatternMessage, SelectMessage, VariableRef  # noqa: E402
from moz.l10n.resource import parse_resource  # noqa: E402

EXTS = (".ftl", ".properties", ".ini")
LABEL_ATTRS = ("label", "value", "placeholder", "tooltiptext", "aria-label", "title", "toolbarname")
# Values that are keyboard input, not prose.
KEY_ATTRS = ("accesskey", "accessKey", "key", "keycode", "commandkey")


def render(msg):
    """Flatten a message to {variant: text}."""
    def pattern(p):
        out = ""
        for el in p:
            if isinstance(el, str):
                out += el
            elif isinstance(el, Expression):
                arg = el.arg
                if isinstance(arg, VariableRef):
                    out += "{$%s}" % arg.name
                elif arg is None:
                    out += "{%s}" % el.function
                else:
                    out += "{%s}" % getattr(arg, "value", arg)
            elif isinstance(el, Markup):
                out += "<%s>" % el.name
        return out

    if isinstance(msg, PatternMessage):
        return {"": pattern(msg.pattern)}
    if isinstance(msg, SelectMessage):
        return {
            " ".join("*" if isinstance(k, CatchallKey) else (k if isinstance(k, str) else k.value)
                     for k in keys): pattern(p)
            for keys, p in msg.variants.items()
        }
    return {}


PLACEHOLDER = re.compile(r"\{\$[^}]+\}|\{-[^}]+\}|%(?:[0-9]+\$)?[Ssd]|#[0-9]")


def load(root):
    out = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("_configs", "_data")]
        for f in files:
            if not f.endswith(EXTS):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            try:
                res = parse_resource(full)
            except Exception as exc:
                out.setdefault(rel, {})["__parse_error__"] = str(exc)
                continue
            entries = out.setdefault(rel, {})
            for section in res.sections:
                for entry in section.entries:
                    if not hasattr(entry, "id"):     # standalone comment
                        continue
                    base =".".join(list(section.id) + list(entry.id))
                    for attr, msg in [("", entry.value)] + sorted(entry.properties.items()):
                        for variant, text in render(msg).items():
                            if attr == "" and not text and entry.properties:
                                continue
                            entries[(base, attr, variant)] = text
    return out


def check(locale_root, ref_root, only, quotes=False):
    problems = []
    loc = load(locale_root)
    ref = load(ref_root) if ref_root and os.path.isdir(ref_root) else {}

    for rel, entries in sorted(loc.items()):
        if only and not any(rel.startswith(p) for p in only):
            continue
        if "__parse_error__" in entries:
            problems.append((rel, "-", "parse error: " + entries["__parse_error__"]))
            continue
        keys = {(k[0], k[1], k[2]): v for k, v in entries.items()}
        for (base, attr, variant), text in entries.items():
            where = base + (f".{attr}" if attr else "") + (f" [{variant}]" if variant else "")

            if attr in KEY_ATTRS or base.split(".")[-1] in KEY_ATTRS:
                label = None
                for a in LABEL_ATTRS + ("",):
                    for v in (variant, ""):
                        if keys.get((base, a, v)):
                            label = keys[(base, a, v)]
                            break
                    if label:
                        break
                if label is None:   # any variant of a label attribute
                    label = next((t for (b, a, _), t in keys.items()
                                  if b == base and a in LABEL_ATTRS and t), None)
                if attr in ("accesskey", "accessKey") or base.endswith((".accesskey", ".accessKey")):
                    src_key = ref.get(rel, {}).get((base, attr, variant))
                    src_label = next((t for (b, a, v), t in ref.get(rel, {}).items()
                                      if b == base and a in LABEL_ATTRS and t), None)
                    upstream_broken = (src_key and src_label
                                       and src_key.lower() not in src_label.lower())
                    if label and len(text) == 1 and text.lower() not in label.lower() \
                            and not upstream_broken:
                        problems.append((rel, where, f"access key {text!r} is not in {label!r}"))
                continue

            fixed = adapt_text(text, quotes=quotes)
            if fixed != text:
                problems.append((rel, where, f"en-US style: {text!r} -> {fixed!r}"))
            if re.search(r"\w'\w", text):
                problems.append((rel, where, "straight apostrophe, use ’"))
            if re.search(r"[.!?] {2,}\S", text):
                problems.append((rel, where, "double space after sentence end"))

            src = ref.get(rel, {}).get((base, attr, variant))
            if src is not None:
                a, b = sorted(PLACEHOLDER.findall(src)), sorted(PLACEHOLDER.findall(text))
                if a != b:
                    problems.append((rel, where, f"placeholders differ from en-US: {a} vs {b}"))

    return problems


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--locale", default=os.path.join(repo, "en-CA"))
    ap.add_argument("--ref", default=os.path.expanduser("~/mozilla-source/git/firefox-quarantine"))
    ap.add_argument("--quotes", action="store_true",
                    help="also flag ‘…’ quotes that en-CA usually writes as “…”")
    args = ap.parse_args()

    only = []
    for p in args.paths:
        p = os.path.abspath(p)
        if p.startswith(os.path.abspath(args.locale)):
            p = os.path.relpath(p, args.locale)
        only.append(p)

    problems = check(args.locale, args.ref, only, quotes=args.quotes)
    for rel, where, msg in problems:
        print(f"{rel}: {where}: {msg}")
    print(f"\n{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
