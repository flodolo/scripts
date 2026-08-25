---
name: backfill-en-ca
description: Fill in missing en-CA translations in this repo from the en-US source, following the established en-CA style (Canadian spelling, typographic apostrophes, en-US wording otherwise). Use when asked to complete, backfill, or update the en-CA locale, or to check en-CA strings against its style rules.
---

# Backfill en-CA

en-CA is en-US with Canadian spelling and a few terminology fixes — 98.9% of
its strings are byte-identical to the source. Backfilling is therefore
mostly mechanical, and the scripts here do the mechanical part; your job is
the ~1% that needs judgement.

**Read `reference/style-rules.md` before writing or reviewing any string.**
`reference/analysis.md` records how those rules were derived and how far they
can be trusted.

## Paths

- locale: `en-CA/` in this repo
- source: `~/mozilla/git/firefox-quarantine` (same relative paths)
- moz.l10n tooling: `~/mozilla/git/firefox-quarantine/.venv/bin/`
  (`l10n-lint`, `l10n-compare`)

Both are overridable with `--locale` / `--ref`.

## Workflow

Run from `.claude/skills/backfill-en-ca/scripts`.

1. **See what is missing** (nothing is written):

   ```bash
   python3 backfill.py --report
   ```

   It prints each missing entry exactly as it would be inserted, with `!!`
   warnings for anything ambiguous. Take a subtree to narrow it down:
   `python3 backfill.py --report browser/browser`.

2. **Review the proposed text before writing.** For every entry check it
   against `reference/style-rules.md`:
   - Canadian spelling applied, `-ize` endings left alone.
   - Nothing changed inside placeables, markup, URLs, or identifiers.
   - Access key present in its own label; if the label's spelling changed,
     pick a letter that is still there.
   - Every `!!` warning resolved by hand (`Cert` → `Certificate`, noun
     *licence* vs verb *license*, and so on).
   - The en-US wording is otherwise kept as-is — do not rephrase.

3. **Apply**:

   ```bash
   python3 backfill.py --apply
   ```

   Entries are inserted at their en-US position with their comments, and a
   `##` group header is added when the group does not exist yet. Existing
   translations are never rewritten and en-CA-only (obsolete) strings are
   never removed.

4. **Fix by hand** whatever step 2 turned up, editing the inserted strings
   directly.

5. **Verify**:

   ```bash
   Q=~/mozilla/git/firefox-quarantine
   $Q/.venv/bin/python check_style.py                 # style rules + access keys + placeholders
   $Q/.venv/bin/l10n-compare --source $Q ../../../../en-CA   # nothing missing
   $Q/.venv/bin/l10n-lint ../../../../en-CA           # parses (ignore "unsupported <file>" lines)
   git -C ../../../.. diff --stat en-CA
   ```

   `check_style.py` should report only the 2 known pre-existing problems
   listed in `reference/analysis.md`; anything else is yours. It takes paths
   to limit the scan, and `--quotes` to also list legacy `‘…’` strings.

## Scripts

- `ca_adapt.py` — the deterministic en-US → en-CA transform (spelling,
  apostrophes, quotes, whitespace) plus the "needs judgement" warnings.
  `python3 ca_adapt.py "some text"` adapts one string;
  `python3 ca_adapt.py --selftest` checks the rules still behave.
  Stdlib only.
- `backfill.py` — finds missing entries and inserts them. Stdlib only.
- `check_style.py` — style/consistency checker. Needs moz.l10n, so run it
  with the quarantine venv's python.

If a rule turns out to be wrong or a new pattern shows up, update
`ca_adapt.py` **and** `reference/style-rules.md` together, then re-run
`ca_adapt.py --selftest`.

## Don't

- Don't remove obsolete strings that exist only in en-CA.
- Don't reword, re-capitalise, or re-punctuate strings that already exist.
- Don't touch `intl.accept_languages` or the hunspell dictionary in
  `en-CA/extensions/spellcheck/`.
- Don't commit or push unless asked.
