#!/usr/bin/env python3
"""Backfill missing en-CA translations from the en-US reference.

For every ``values-en-rCA/*.xml`` file, compares the string IDs against the
matching ``values/*.xml`` reference and inserts any missing entry at the same
position as in en-US, carrying over its comment block, attributes and
indentation verbatim. Canadian spelling rules (see ../rules.md) are then
applied to the inserted string values only.

Obsolete entries (present in en-CA, absent from en-US) are reported but never
removed. Existing en-CA translations are never modified.

Usage:
    python3 backfill_en_ca.py [--dry-run] [--repo PATH] [--filter SUBSTRING]
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from xml.etree import ElementTree as ET

# --------------------------------------------------------------------------
# Canadian spelling rules
#
# AUTO_RULES are applied unconditionally to inserted string values.
# REVIEW_RULES are never applied: they are context dependent, so the script
# only flags them for a human (or Claude) to decide.
# See ../rules.md for the rationale and the corpus evidence behind each entry.
# --------------------------------------------------------------------------

# (pattern, replacement) applied case-insensitively while preserving the case
# of the original match.
AUTO_RULES: list[tuple[str, str]] = [
    # 1. -or -> -our
    (r"\bcolor\b", "colour"),
    (r"\bcolors\b", "colours"),
    (r"\bcolored\b", "coloured"),
    (r"\bcoloring\b", "colouring"),
    (r"\bcolorful\b", "colourful"),
    (r"\bcolorless\b", "colourless"),
    (r"\bmulticolor\b", "multicolour"),
    (r"\bfavorite\b", "favourite"),
    (r"\bfavorites\b", "favourites"),
    (r"\bfavor\b", "favour"),
    (r"\bfavors\b", "favours"),
    (r"\bfavored\b", "favoured"),
    (r"\bfavoring\b", "favouring"),
    (r"\bfavorable\b", "favourable"),
    (r"\bfavorably\b", "favourably"),
    (r"\bbehavior\b", "behaviour"),
    (r"\bbehaviors\b", "behaviours"),
    (r"\bbehavioral\b", "behavioural"),
    (r"\bneighbor\b", "neighbour"),
    (r"\bneighbors\b", "neighbours"),
    (r"\bneighboring\b", "neighbouring"),
    (r"\bneighborhood\b", "neighbourhood"),
    (r"\bneighborhoods\b", "neighbourhoods"),
    (r"\bhonor\b", "honour"),
    (r"\bhonors\b", "honours"),
    (r"\bhonored\b", "honoured"),
    (r"\bhonorable\b", "honourable"),
    (r"\bhumor\b", "humour"),
    # NB: 'humorous', 'rigorous', 'vigorous', 'honorary' keep the US -or form.
    (r"\blabor\b", "labour"),
    (r"\blabors\b", "labours"),
    (r"\brumor\b", "rumour"),
    (r"\brumors\b", "rumours"),
    (r"\bsavor\b", "savour"),
    (r"\bflavor\b", "flavour"),
    (r"\bflavors\b", "flavours"),
    (r"\bharbor\b", "harbour"),
    (r"\bodor\b", "odour"),
    (r"\bvapor\b", "vapour"),
    (r"\bvalor\b", "valour"),
    (r"\bendeavor\b", "endeavour"),
    (r"\barmor\b", "armour"),
    (r"\bvigor\b", "vigour"),
    (r"\bsplendor\b", "splendour"),
    (r"\bclamor\b", "clamour"),
    (r"\bdemeanor\b", "demeanour"),
    (r"\bparlor\b", "parlour"),
    (r"\bcandor\b", "candour"),
    (r"\btumor\b", "tumour"),
    (r"\bsavior\b", "saviour"),
    # 2. single -l- -> doubled -ll- before a vowel suffix
    (r"\bcanceled\b", "cancelled"),
    (r"\bcanceling\b", "cancelling"),
    (r"\bcancelation\b", "cancellation"),
    (r"\btraveled\b", "travelled"),
    (r"\btraveling\b", "travelling"),
    (r"\btraveler\b", "traveller"),
    (r"\btravelers\b", "travellers"),
    (r"\blabeled\b", "labelled"),
    (r"\blabeling\b", "labelling"),
    (r"\bunlabeled\b", "unlabelled"),
    (r"\bmodeled\b", "modelled"),
    (r"\bmodeling\b", "modelling"),
    (r"\bfueled\b", "fuelled"),
    (r"\bfueling\b", "fuelling"),
    (r"\brefueled\b", "refuelled"),
    (r"\bsignaled\b", "signalled"),
    (r"\bsignaling\b", "signalling"),
    (r"\btotaled\b", "totalled"),
    (r"\btotaling\b", "totalling"),
    (r"\bleveled\b", "levelled"),
    (r"\bleveling\b", "levelling"),
    (r"\bdialed\b", "dialled"),
    (r"\bdialing\b", "dialling"),
    (r"\bmarveled\b", "marvelled"),
    (r"\bcounseled\b", "counselled"),
    (r"\bcounseling\b", "counselling"),
    (r"\bequaled\b", "equalled"),
    (r"\bfulfilled\b", "fulfilled"),  # no-op, guards against over-eager edits
    # 3. -yze -> -yse  (but not analysis / analytics / analyst)
    (r"\banalyze\b", "analyse"),
    (r"\banalyzes\b", "analyses"),
    (r"\banalyzed\b", "analysed"),
    (r"\banalyzing\b", "analysing"),
    (r"\bparalyze\b", "paralyse"),
    (r"\bparalyzed\b", "paralysed"),
    (r"\bcatalyze\b", "catalyse"),
    (r"\bbreathalyze\b", "breathalyse"),
    # 4. -er -> -re
    (r"\bcenter\b", "centre"),
    (r"\bcenters\b", "centres"),
    (r"\bcentered\b", "centred"),
    (r"\btheater\b", "theatre"),
    (r"\btheaters\b", "theatres"),
    (r"\bliter\b", "litre"),
    (r"\bliters\b", "litres"),
    (r"\bfiber\b", "fibre"),
    (r"\bfibers\b", "fibres"),
    (r"\bcaliber\b", "calibre"),
    # 5. misc
    (r"\bgray\b", "grey"),
    (r"\bgrays\b", "greys"),
    (r"\bgrayed\b", "greyed"),
    (r"\bgrayscale\b", "greyscale"),
    (r"\bdefense\b", "defence"),
    (r"\bdefenses\b", "defences"),
    (r"\boffense\b", "offence"),
    (r"\boffenses\b", "offences"),
    (r"\bpretense\b", "pretence"),
    (r"\bstorey\b", "storey"),
]

# Words that need a human decision. (pattern, note)
REVIEW_RULES: list[tuple[str, str]] = [
    (r"\blicense[sd]?\b",
     "noun -> 'licence' (a licence), verb stays 'license' (to license). "
     "Leave 'License' alone inside the MPL header or a licence name."),
    (r"\bpractice[sd]?\b",
     "noun stays 'practice', verb -> 'practise'."),
    (r"\bdialogs?\b",
     "UI/technical sense stays 'dialog' (matches the existing corpus); "
     "'a dialogue' in the conversational sense -> 'dialogue'."),
    (r"\bcatalogs?\b",
     "generic listing -> 'catalogue'; keep 'catalog' if it names an API/field."),
    (r"\banalogs?\b", "generic -> 'analogue'; keep 'analog' in a technical name."),
    (r"\bmeters?\b",
     "unit of length -> 'metre'; a measuring device stays 'meter'."),
    (r"\benroll(ed|ing|ment)?\b",
     "Canadian usage is mixed; prefer 'enrol'/'enrolment' unless the "
     "surrounding strings already use the doubled form."),
    (r"\bfulfill(ed|ing|ment)?\b",
     "prefer 'fulfil'/'fulfilment' for the bare stem; 'fulfilled'/'fulfilling' "
     "keep the double l."),
    (r"\binstallments?\b", "-> 'instalment' (one l) when it means a payment."),
    (r"\bskillful\b", "-> 'skilful'."),
    (r"\bwillful\b", "-> 'wilful'."),
    (r"\bjudgment\b",
     "Canadian legal writing keeps 'judgment'; general prose often uses "
     "'judgement'. Match neighbouring strings."),
    (r"\backnowledgment\b", "-> 'acknowledgement' in general prose."),
    (r"\bcheck\b",
     "'check' (verify, checkbox) is correct; only a bank instrument becomes "
     "'cheque'."),
    (r"\bAI(?:-powered)?\s+enhancements?\b|\bAI-powered\s+features?\b",
     "the existing en-CA strings render 'AI enhancements' / 'AI-powered "
     "features' as 'features with AI'. Reuse that wording only if it reads "
     "naturally here; otherwise keep the en-US phrasing."),
]

# Deliberate non-changes: en-GB makes these substitutions, en-CA does not.
# Kept here as documentation and asserted by --self-check.
KEEP_US_FORMS = [
    "website", "websites", "webpage", "webpages", "Sync", "sync", "synced",
    "syncing", "back", "forward", "State", "Zip", "Postal Code", "cart",
    "cellular", "program", "aluminum", "tire", "curb",
    # -ize / -ization family is Canadian too
    "organize", "organization", "customize", "summarize", "recognize",
    "authorize", "optimize", "synchronize", "personalize", "prioritize",
    "apologize", "realize", "finalize", "maximize", "minimize", "utilize",
    "capitalize",
]

ELEMENT_START = re.compile(r"^\s*<(string|plurals|string-array)[\s>]")
NAME_ATTR = re.compile(r'\bname="([^"]+)"')


def match_case(replacement: str, original: str) -> str:
    """Carry the original token's capitalization over to the replacement."""
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def apply_spelling(value: str) -> tuple[str, list[str]]:
    """Return (canadianized value, list of applied rule descriptions)."""
    applied = []
    for pattern, replacement in AUTO_RULES:
        def sub(m, replacement=replacement):
            new = match_case(replacement, m.group(0))
            if new != m.group(0):
                applied.append(f"{m.group(0)} -> {new}")
            return new

        value = re.sub(pattern, sub, value, flags=re.IGNORECASE)
    return value, applied


def find_review_flags(value: str) -> list[str]:
    flags = []
    for pattern, note in REVIEW_RULES:
        m = re.search(pattern, value, flags=re.IGNORECASE)
        if m:
            flags.append(f"“{m.group(0)}”: {note}")
    return flags


class Block:
    """A comment block plus the entity it documents, as raw lines."""

    __slots__ = ("key", "lines")

    def __init__(self, key, lines):
        self.key = key
        self.lines = lines


def split_file(path: str) -> tuple[list[str], list[Block], list[str]]:
    """Split a strings.xml into (header lines, entity blocks, footer lines)."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    # Header: everything up to and including the <resources ...> open tag.
    start = 0
    for i, line in enumerate(lines):
        if "<resources" in line:
            start = i + 1
            break
    header = lines[:start]

    end = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if "</resources>" in lines[i]:
            end = i
            break
    footer = lines[end:]

    body = lines[start:end]
    blocks: list[Block] = []
    pending: list[str] = []
    i = 0
    while i < len(body):
        line = body[i]
        stripped = line.strip()
        if stripped.startswith("<!--"):
            # Consume the whole comment, however many lines it spans.
            pending.append(line)
            while "-->" not in body[i]:
                i += 1
                pending.append(body[i])
            i += 1
            continue
        m = ELEMENT_START.match(line)
        if m:
            tag = m.group(1)
            chunk = [line]
            if tag != "string" and f"</{tag}>" not in stripped:
                while f"</{tag}>" not in body[i]:
                    i += 1
                    chunk.append(body[i])
            name = NAME_ATTR.search(line)
            key = f"{tag}:{name.group(1)}" if name else f"{tag}:?{len(blocks)}"
            blocks.append(Block(key, pending + chunk))
            pending = []
            i += 1
            continue
        # Blank lines and anything unexpected attach to the next block.
        pending.append(line)
        i += 1

    if pending:
        footer = pending + footer
    return header, blocks, footer


def canadianize_block(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Apply spelling rules to element content only, never to comments."""
    out, applied, flags = [], [], []
    in_comment = False
    for line in lines:
        stripped = line.strip()
        if in_comment:
            out.append(line)
            if "-->" in line:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            out.append(line)
            if "-->" not in line:
                in_comment = True
            continue

        def repl(m):
            new_value, a = apply_spelling(m.group(1))
            applied.extend(a)
            flags.extend(find_review_flags(new_value))
            return ">" + new_value + "<"

        # Only the text between an opening and closing tag on the same line.
        out.append(re.sub(r">([^<>]*)<", repl, line))
    return out, applied, flags


def process(ref_path: str, l10n_path: str, rel: str, dry_run: bool) -> dict:
    ref_header, ref_blocks, _ = split_file(ref_path)
    ca_header, ca_blocks, ca_footer = split_file(l10n_path)

    ref_keys = [b.key for b in ref_blocks]
    ca_keys = [b.key for b in ca_blocks]

    ref_set, ca_set = set(ref_keys), set(ca_keys)
    missing = [k for k in ref_keys if k not in ca_set]
    obsolete = [k for k in ca_keys if k not in ref_set]

    result = {
        "file": rel,
        "missing": missing,
        "obsolete": obsolete,
        "added": [],
        "applied": [],
        "flags": [],
    }
    if not missing:
        return result

    # Splice the en-US blocks into the en-CA sequence at the aligned position.
    matcher = difflib.SequenceMatcher(None, ca_keys, ref_keys, autojunk=False)
    merged: list[Block] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            merged.extend(ca_blocks[i1:i2])
        elif tag == "delete":
            merged.extend(ca_blocks[i1:i2])  # obsolete: keep as-is
        elif tag == "insert":
            merged.extend(insert_ref(ref_blocks[j1:j2], result))
        elif tag == "replace":
            merged.extend(ca_blocks[i1:i2])
            merged.extend(insert_ref(ref_blocks[j1:j2], result))

    new_text = "".join(ca_header + [l for b in merged for l in b.lines] + ca_footer)

    if not dry_run:
        ET.fromstring(new_text)  # fail loudly rather than write broken XML
        with open(l10n_path, "w", encoding="utf-8") as fh:
            fh.write(new_text)
    return result


def insert_ref(blocks: list[Block], result: dict) -> list[Block]:
    out = []
    for b in blocks:
        lines, applied, flags = canadianize_block(b.lines)
        out.append(Block(b.key, lines))
        value = ""
        for line in lines:
            m = re.search(r">([^<>]+)</(?:string|item)>", line)
            if m:
                value = m.group(1)
                break
        result["added"].append((b.key, value))
        result["applied"].extend(f"{b.key}: {a}" for a in applied)
        result["flags"].extend(f"{b.key}: {f}" for f in flags)
    return out


def self_check(repo: str) -> int:
    """Verify AUTO_RULES never contradict the existing en-CA corpus."""
    problems = 0
    for l10n, _ref, rel in locale_files(repo, None):
        _, blocks, _ = split_file(l10n)
        for b in blocks:
            for line in b.lines:
                if line.strip().startswith("<!--"):
                    continue
                for m in re.finditer(r">([^<>]+)</(?:string|item)>", line):
                    new, applied = apply_spelling(m.group(1))
                    if applied:
                        print(f"CONTRADICTION {rel} {b.key}: {applied}")
                        problems += 1
    print(f"self-check: {problems} contradiction(s) against the existing en-CA corpus")
    return problems


def locale_files(repo: str, flt: str | None):
    for dirpath, dirnames, filenames in os.walk(os.path.join(repo, "mozilla-mobile")):
        if os.path.basename(dirpath) != "values-en-rCA":
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            l10n = os.path.join(dirpath, fn)
            ref = os.path.join(dirpath.replace("values-en-rCA", "values"), fn)
            rel = os.path.relpath(l10n, repo)
            if flt and flt not in rel:
                continue
            if not os.path.exists(ref):
                print(f"WARNING: no en-US reference for {rel}", file=sys.stderr)
                continue
            yield l10n, ref, rel


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.getcwd(), help="repository root")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    ap.add_argument("--filter", help="only process paths containing this substring")
    ap.add_argument("--self-check", action="store_true",
                    help="assert AUTO_RULES agree with the existing en-CA corpus")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if args.self_check:
        return 1 if self_check(repo) else 0

    results = [process(ref, l10n, rel, args.dry_run)
               for l10n, ref, rel in locale_files(repo, args.filter)]

    total_added = total_obsolete = 0
    for r in results:
        total_obsolete += len(r["obsolete"])
        if not r["added"] and not r["obsolete"]:
            continue
        print(f"\n{r['file']}")
        for key, value in r["added"]:
            print(f"  + {key} = {value}")
            total_added += 1
        for key in r["obsolete"]:
            print(f"  · obsolete (kept): {key}")
        for a in dict.fromkeys(r["applied"]):
            print(f"  ~ spelling: {a}")
        for f in dict.fromkeys(r["flags"]):
            print(f"  ! review: {f}")

    verb = "would add" if args.dry_run else "added"
    print(f"\n{verb} {total_added} string(s); {total_obsolete} obsolete entr(ies) kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
