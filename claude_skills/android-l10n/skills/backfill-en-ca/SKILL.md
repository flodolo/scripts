---
name: backfill-en-ca
description: Fill in missing en-CA (English, Canada) translations in this repository from the en-US reference, applying Canadian English spelling. Use when asked to backfill, complete, sync, or add missing en-CA strings, or to check en-CA for completeness against en-US.
---

# Backfill missing en-CA translations

en-CA is maintained in-repo rather than translated from scratch: each
`values-en-rCA/strings.xml` is a mirror of its `values/strings.xml` en-US
reference with Canadian spelling applied to the string values only. Backfilling
is therefore a mechanical copy plus a spelling pass — not a translation task.

Read `rules.md` before touching any string. It is the output of a full
en-CA/en-US corpus analysis and records both the rules to apply and the traps
(en-CA keeps `-ize`, keeps `website`, keeps `Zip`/`State` — do not copy en-GB).

## Workflow

**1. Survey what is missing.**

```bash
python3 .claude/skills/backfill-en-ca/scripts/backfill_en_ca.py --dry-run
```

Add `--filter fenix` (or any path substring) to narrow the run. Report the
counts to the user before writing anything.

**2. Apply the backfill.**

```bash
python3 .claude/skills/backfill-en-ca/scripts/backfill_en_ca.py
```

For each missing entry the script copies the en-US lines verbatim — comment
block, attributes, indentation — into the position that matches en-US, then
rewrites only the text inside `<string>` / `<item>` using the automatic rules.
It validates the XML before writing, so a failure means nothing was written.

Obsolete entries (present in en-CA, absent from en-US) are reported with `·`
and **kept**. Existing en-CA translations are never modified. If the user asks
for something that would change or remove an existing translation, say so and
stop — that is outside this skill.

**3. Resolve every `! review:` line by hand.**

These are the context-dependent words the script deliberately refuses to guess
(`licence` vs `license`, `dialog` vs `dialogue`, `metre` vs `meter`, …). Look at
the string's own comment and at neighbouring strings in the same file to decide,
then edit the value with `Edit`. The review table in `rules.md` gives the
decision criteria for each.

Also re-read each added value against the rules for anything the regex table
cannot catch — a US-only idiom, or a `-our`/`-ll-`/`-yse` word not yet in the
table. If you find a genuinely new rule, add it to `AUTO_RULES` (or
`REVIEW_RULES`) in the script *and* document it in `rules.md`, then re-run
step 4.

**4. Verify.**

```bash
# the rule table must not contradict any existing en-CA translation
python3 .claude/skills/backfill-en-ca/scripts/backfill_en_ca.py --self-check
# nothing left to add
python3 .claude/skills/backfill-en-ca/scripts/backfill_en_ca.py --dry-run
# every touched file still parses
git diff --name-only | xargs -I{} python3 -c "import sys,xml.etree.ElementTree as E; E.parse('{}')"
```

Then read `git diff`. The added blocks should be indistinguishable from the
en-US reference except for the Canadianized values. A useful stronger check: the
en-CA file should now be structurally identical to en-US, so a diff of the two
files with all string values masked should be empty.

**5. Report, do not commit.**

Summarize what was added per file, which review flags you resolved and how, and
which obsolete entries were left in place. Leave committing and pushing to the
user.

## Adding a new rule

`AUTO_RULES` in `scripts/backfill_en_ca.py` is a list of
`(case-insensitive regex, replacement)` pairs applied to inserted string values;
the replacement inherits the original token's capitalization. Use `\b`
anchors and spell out inflections explicitly rather than writing a broad suffix
pattern — over-eager patterns are the main risk here. `--self-check` re-applies
the whole table to every existing en-CA value and fails if any rule would have
changed a string a human already approved; keep it at zero.

Put anything that depends on meaning in `REVIEW_RULES` with a note explaining
the choice, never in `AUTO_RULES`.
