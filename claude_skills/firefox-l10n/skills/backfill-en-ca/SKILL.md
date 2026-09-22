---
name: backfill-en-ca
description: Fill in missing translations in en-CA/firefox-ios.xliff by adapting the en-US source into Canadian English, following the style already established in the file. Use when asked to complete, backfill, or fill the untranslated strings in en-CA (English, Canada), or to check how many en-CA strings are missing.
---

# Backfill missing en-CA translations

`en-CA/firefox-ios.xliff` is a same-language localization: it starts from the
`en-US` reference and changes only what Canadian English requires. Almost
everything is a verbatim copy of the source, so backfilling is mostly mechanical
— the value is in getting the handful of real deviations right and in not
touching anything else.

## Hard constraints

- **Only add `<target>` elements** to `<trans-unit>`s that currently have none.
  Never modify, reorder, or delete an existing `<target>`, `<source>`, `<note>`,
  or `<trans-unit>`.
- **Never remove obsolete strings.** Units whose ID/file pair no longer exists in
  `en-US` stay exactly as they are. Do not add targets to them either — Pontoon
  removes them on its own schedule.
- Only `en-CA/firefox-ios.xliff` is edited. `en-US/`, `templates/`, other locales,
  and `.github/` are out of scope.
- A new `<target>` goes immediately after `<source>`, before `<note>`, with no
  attributes (no `state`, no `xml:space` — that lives on the `trans-unit`).
- Do not hand-edit the XML. Use `scripts/apply_targets.py`, which writes through
  the repo's `write_xliff()` and round-trips the file byte-identically (verified).

## Workflow

1. **List what's missing**

   ```bash
   .venv/bin/python .claude/skills/backfill-en-ca/scripts/report_untranslated.py
   ```

   Writes `/tmp/en-CA-missing.json` (`[{file, id, source, note}, ...]`) and prints
   a summary: translated / missing / obsolete counts. Obsolete units are reported
   for information only.

2. **Translate** each entry by applying the rules below. Produce a JSON file
   shaped like:

   ```json
   [{"file": "Client/en.lproj/Localizable.strings", "id": "Foo.Bar.v155", "target": "…"}]
   ```

   `file` + `id` together are the key — IDs repeat across `<file>` sections
   (15 duplicates today), so `id` alone is ambiguous.

   Work in batches you can eyeball. Most entries will be a verbatim copy of
   `source`; spend the attention on the ones that aren't.

3. **Apply**

   ```bash
   .venv/bin/python .claude/skills/backfill-en-ca/scripts/apply_targets.py /tmp/en-CA-new.json
   ```

   Refuses to overwrite an existing target or to touch a unit missing from
   `en-US`, and reports anything it skipped.

4. **Verify**

   ```bash
   .venv/bin/python .claude/skills/backfill-en-ca/scripts/check_style.py
   git diff --stat en-CA/
   git diff en-CA/ | grep -c '^-'   # expect 1 (the --- diff header) — no deletions
   ```

   `check_style.py` flags placeholder mismatches, typography drift, leftover
   American `-our`/`-re` spellings, and over-applied `-ise`/`-yse` forms. Read its
   output and fix real hits; it also re-reports pre-existing legacy deviations, so
   compare against a run on a clean checkout if unsure.

5. Report to the user how many targets were added and list every string where you
   deviated from a verbatim copy, with the reason. Do not commit unless asked.

## Style rules

Derived from a full comparison of the 1,847 existing en-CA targets against
`en-US` (25 differ from source; the rest are byte-identical).

### R1 — Default: copy the source verbatim

98.6% of existing targets equal their source exactly. If no rule below applies,
the target is the source string, character for character.

### R2 — `-our` spellings (always applied, 8/8)

`color → colour`, `favorite → favourite`, `neighborhood → neighbourhood`, and the
same for inflections (`colors → colours`, `colored`, `favourites`). Extend to
`behaviour`, `honour`, `labour`, `flavour`, `humour`, `rumour`, `odour`,
`vapour`, `savour`, `endeavour` if they appear.

Exception, as in British English: `-orous`/`-oration` derivatives keep the short
form — `humorous`, `coloration`, `honorary`, `laborious`.

### R3 — `-re` spellings (applied, 1/1)

`center → centre` (`centered → centred`, `centre of the toolbar`). Same for
`theatre`, `fibre`, `litre`, `metre` **as a unit of length**. Keep `meter` when it
means a measuring device or a UI meter.

### R4 — Keep `-ize` / `-yze` (never changed, 22/22)

Canadian English uses the `-ize` forms, same as en-US. Do **not** switch to
`-ise`/`-yse`: `customize`, `customization`, `organization`, `personalize`,
`summarize`, `recognize`, `optimize`, `synchronize`, `realize`, `analyze`,
`paralyze` all stay.

### R5 — Keep these American forms (never changed in en-CA)

`license` / `Licenses` (noun and verb — do not write `licence`), `install`,
`practice`, `program`, `check` (verb and noun — never `cheque`), `tire`,
`defense`, `offense`, `dialog` (UI sense), `catalog`, `gray` when it appears in a
technical/colour-token context. Evidence: `license` 1/1, `install` 2/2, `check`
6/6 unchanged.

### R6 — Doubled consonants (low evidence — flag it)

Canadian English prefers `travelled`, `cancelled`, `labelled`, `modelled`,
`fuelled`, `marvellous`, `enrolled`. The one existing data point
(`Download Cancelled`) already had the doubled form in the source, so the file
doesn't actually settle this. Apply the doubled form, and call it out explicitly
in your report so the user can veto it.

### R7 — Typography must match the source exactly

Copy the source's punctuation characters as-is: curly apostrophe `’` (never `'`),
ellipsis `…` (never `...`), em dash `—` (never `-`), en dash `–`, curly quotes,
narrow/non-breaking spaces, emoji. This was fixed by hand once already (commit
`6b4ba8b`, "en-GB/en-CA: fix typography consistency with en-US") — don't
reintroduce it. The file stores literal Unicode, never numeric entities.

### R8 — Placeholders are untouchable

`%@`, `%1$@`, `%2$@`, `%d`, `%1$d` must appear the same number of times, in the
same order, with the same indices as in the source. Never reorder, renumber,
translate, or add spacing around them.

### R9 — Preserve the source's capitalization

Copy the source's case. The existing file has ~8 case-only deviations in both
directions (`Get Help → Get help`, `Recently Closed → Recently closed`, but also
`New tab → New Tab`, `Card Removed → Card removed`). These are inconsistent
legacy noise — do not imitate the pattern and do not "fix" the existing entries.

### R10 — Preserve whitespace

Copy leading/trailing spaces and embedded newlines from the source. (Some legacy
targets stripped a trailing space or collapsed a newline; treat those as
artifacts, not precedent.)

### R11 — Never translate brand and proper names

`Firefox`, `Focus`, `Klar`, `Pocket`, `Mozilla`, `Wayback Machine`,
`Internet Archive`, `Face ID`, `Wi-Fi`, `iOS`, `Wrexham A.F.C.`, and anything
supplied through a placeholder.

### R12 — Don't generalize one-off wording changes

The file contains a single lexical substitution (`Log in → Sign in`). Treat it as
a historical one-off: keep the source's wording everywhere else. If a new string
seems to need a wording change beyond spelling, leave it as the source and raise
it with the user instead of inventing a house style.

### R13 — Fixing source typos

`An error occured → An error occurred` was corrected in en-CA. Obvious source
typos may be fixed silently in the target, but always report them so the user can
file the fix upstream in `firefox-ios`.
