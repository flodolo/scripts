#!/usr/bin/env python3
"""Backfill missing en-CA strings from the en-US source.

For every en-US file it finds the entries that are absent from the matching
en-CA file and inserts them at the same position as in en-US, together with
their comments (and their ``##`` group header if that group does not exist
yet). Entries present only in en-CA (obsolete strings) are never touched, and
existing en-CA translations are never rewritten.

Values are passed through ca_adapt.adapt_text(); everything that needs a
judgement call is listed in the report so it can be reviewed afterwards.

Usage:
    backfill.py --report                 # list what is missing, change nothing
    backfill.py --apply                  # write the files
    backfill.py --apply browser/browser  # limit to a subtree (path relative to the locale root)

Options:
    --locale DIR   en-CA root      (default: <repo>/en-CA)
    --ref DIR      en-US root      (default: ~/mozilla-source/git/firefox-quarantine)
    --json FILE    write the report as JSON
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ca_adapt import adapt_text, warnings  # noqa: E402

EXTS = (".ftl", ".properties", ".ini")
SKIP_DIRS = {".git", ".venv", "_configs", "_data", "node_modules"}

FTL_KEY = re.compile(r"^(-?[A-Za-z][A-Za-z0-9_-]*)\s*=")
PROP_KEY = re.compile(r"^([^#!;\[\s][^=:]*?)\s*[=:]")
INI_SECTION = re.compile(r"^\[[^\]]+\]\s*$")


class Unit:
    """A run of lines: one entry (with its comment), a group header, or filler."""

    def __init__(self, kind, key, lines):
        self.kind = kind      # 'entry' | 'group' | 'filler'
        self.key = key        # entry key, or group header text
        self.lines = lines

    def __repr__(self):
        return f"Unit({self.kind}, {self.key!r}, {len(self.lines)} lines)"


def parse_ftl(lines):
    units, i, pending = [], 0, []
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("###"):
            units.append(Unit("filler", None, pending + [line]))
            pending, i = [], i + 1
        elif line.startswith("##"):
            block = pending + [line]
            i += 1
            while i < n and lines[i].startswith("##"):
                block.append(lines[i])
                i += 1
            units.append(Unit("group", "\n".join(block).strip(), block))
            pending = []
        elif line.startswith("#"):
            pending.append(line)
            i += 1
        elif line.strip() == "":
            if pending:                      # comment not attached to an entry
                units.append(Unit("filler", None, pending))
                pending = []
            units.append(Unit("filler", None, [line]))
            i += 1
        else:
            m = FTL_KEY.match(line)
            if not m:                        # unexpected content: keep verbatim
                units.append(Unit("filler", None, pending + [line]))
                pending, i = [], i + 1
                continue
            block = pending + [line]
            i += 1
            while i < n:
                nxt = lines[i]
                if nxt.strip() == "":
                    # blank line belongs to the entry only if an indented line follows
                    j = i
                    while j < n and lines[j].strip() == "":
                        j += 1
                    if j < n and lines[j][:1] in " \t":
                        block.extend(lines[i:j + 1])
                        i = j + 1
                        continue
                    break
                if nxt[:1] in " \t":
                    block.append(nxt)
                    i += 1
                    continue
                break
            units.append(Unit("entry", m.group(1), block))
            pending = []
    if pending:
        units.append(Unit("filler", None, pending))
    return units


def parse_props(lines):
    units, i, pending = [], 0, []
    n = len(lines)
    while i < n:
        line = lines[i]
        if line[:1] in "#!;":
            pending.append(line)
            i += 1
        elif line.strip() == "":
            if pending:
                units.append(Unit("filler", None, pending))
                pending = []
            units.append(Unit("filler", None, [line]))
            i += 1
        elif INI_SECTION.match(line):
            units.append(Unit("group", line.strip(), pending + [line]))
            pending, i = [], i + 1
        else:
            m = PROP_KEY.match(line)
            if not m:
                units.append(Unit("filler", None, pending + [line]))
                pending, i = [], i + 1
                continue
            block = pending + [line]
            i += 1
            while block[-1].endswith("\\") and i < n:   # line continuation
                block.append(lines[i])
                i += 1
            units.append(Unit("entry", m.group(1).strip(), block))
            pending = []
    if pending:
        units.append(Unit("filler", None, pending))
    return units


def parse(path, text):
    lines = text.split("\n")
    return (parse_ftl if path.endswith(".ftl") else parse_props)(lines)


# --- adapting an entry block ----------------------------------------------

def adapt_block(path, lines):
    """Adapt the values in an entry block, leaving keys and comments alone."""
    out, seen_key = [], False
    for line in lines:
        stripped = line.lstrip()
        if stripped[:1] in "#" or (not path.endswith(".ftl") and stripped[:1] in "!;"):
            out.append(line)
            continue
        if not seen_key or (path.endswith(".ftl") and re.match(r"^\s*(\.[A-Za-z-]+|\*?\[[^\]]+\])\s*=", line)):
            head, sep, val = line.partition("=")
            if sep:
                out.append(head + sep + adapt_text(val))
                seen_key = True
                continue
        out.append(adapt_text(line))
    return out


def write_lines(path, lines):
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    open(path, "w", encoding="utf-8").write(text)


def entry_text(lines):
    return "\n".join(lines)


# --- merge -----------------------------------------------------------------

def backfill_file(rel, ref_path, loc_path, apply_changes):
    ref_text = open(ref_path, encoding="utf-8").read()
    ref_units = parse(ref_path, ref_text)
    ref_entries = [u for u in ref_units if u.kind == "entry"]

    if not os.path.exists(loc_path):
        added = [u.key for u in ref_entries]
        new_lines = []
        for u in ref_units:
            new_lines.extend(adapt_block(ref_path, u.lines) if u.kind == "entry" else u.lines)
        if apply_changes:
            os.makedirs(os.path.dirname(loc_path), exist_ok=True)
            write_lines(loc_path, new_lines)
        return added, [(u.key, entry_text(adapt_block(ref_path, u.lines))) for u in ref_entries], True

    loc_units = parse(loc_path, open(loc_path, encoding="utf-8").read())
    loc_keys = {u.key for u in loc_units if u.kind == "entry"}
    missing = [u for u in ref_entries if u.key not in loc_keys]
    if not missing:
        return [], [], False

    # group header currently in effect, per en-US unit
    group_of, current = {}, None
    for u in ref_units:
        if u.kind == "group":
            current = u
        elif u.kind == "entry":
            group_of[u.key] = current
    loc_groups = {u.key for u in loc_units if u.kind == "group"}

    ref_order = [u.key for u in ref_entries]
    added, inserted_text = [], []
    for u in missing:
        block = adapt_block(ref_path, u.lines)
        group = group_of.get(u.key)
        pos = insert_position(loc_units, ref_order, u.key, group)

        prefix = []
        if group is not None and group.key not in loc_groups:
            before = loc_units[pos - 1].lines[-1] if pos else ""
            after = loc_units[pos].lines[0] if pos < len(loc_units) else ""
            prefix = ([""] if before.strip() else []) + group.lines \
                + ([""] if after.strip() else [])
            loc_groups.add(group.key)
        new_units = []
        if prefix:
            new_units.append(Unit("group", group.key, prefix))
        new_units.append(Unit("entry", u.key, block))
        loc_units[pos:pos] = new_units
        added.append(u.key)
        inserted_text.append((u.key, entry_text(block)))

    if apply_changes:
        out = []
        for u in loc_units:
            out.extend(u.lines)
        write_lines(loc_path, out)
    return added, inserted_text, False


def insert_position(loc_units, ref_order, key, group):
    """Index in loc_units where `key` should go, mirroring the en-US order."""
    idx = ref_order.index(key)
    loc_pos = {u.key: i for i, u in enumerate(loc_units) if u.kind == "entry"}

    for prev in reversed(ref_order[:idx]):          # after the closest preceding sibling
        if prev in loc_pos:
            return loc_pos[prev] + 1
    for nxt in ref_order[idx + 1:]:                 # else before the closest following one
        if nxt in loc_pos:
            pos = loc_pos[nxt]
            while pos > 0 and loc_units[pos - 1].kind == "filler" \
                    and loc_units[pos - 1].lines and loc_units[pos - 1].lines[0].startswith("#"):
                pos -= 1                            # keep its comment attached
            return pos
    return len(loc_units)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="limit to these subpaths (relative to the locale root)")
    ap.add_argument("--locale", default=os.path.join(repo, "en-CA"))
    ap.add_argument("--ref", default=os.path.expanduser("~/mozilla-source/git/firefox-quarantine"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()
    if not (args.apply or args.report):
        args.report = True

    report = []
    for dirpath, dirs, files in os.walk(args.ref):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if not f.endswith(EXTS):
                continue
            ref_path = os.path.join(dirpath, f)
            rel = os.path.relpath(ref_path, args.ref)
            if args.paths and not any(rel.startswith(p.rstrip("/")) for p in args.paths):
                continue
            loc_path = os.path.join(args.locale, rel)
            added, texts, new_file = backfill_file(rel, ref_path, loc_path, args.apply)
            if added:
                report.append({
                    "file": rel,
                    "new_file": new_file,
                    "added": added,
                    "entries": [{"key": k, "text": t, "warnings": warnings(t)} for k, t in texts],
                })

    total = sum(len(r["added"]) for r in report)
    for r in report:
        print(f"\n=== {r['file']}{'  (new file)' if r['new_file'] else ''}  [{len(r['added'])}]")
        for e in r["entries"]:
            print(e["text"])
            for w in e["warnings"]:
                print(f"    !! {w}")
    print(f"\n{total} entries in {len(report)} files"
          f"{' — written' if args.apply else ' — dry run, nothing written'}")
    if args.json:
        json.dump(report, open(args.json, "w"), indent=2)


if __name__ == "__main__":
    main()
