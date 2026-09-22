---
name: backfill-locale
description: Translate the strings a locale has not translated yet in firefox-ios.xliff, and upload them to Pontoon as pretranslations. Use when asked to backfill, complete, fill in, or pretranslate a locale (e.g. "backfill it", "complete the missing Italian strings", "pretranslate fr"), or to report how complete a locale is against the en-US reference.
---

# Backfill a locale

Fill the gap between a locale's `firefox-ios.xliff` and the en-US reference,
then publish the result through Pontoon's pretranslation API.

Two things shape the whole workflow:

- **The locale files in this repository are written by Pontoon's sync** (see the
  `Pontoon/Firefox for iOS: Update …` commits). Never hand-edit a `<target>` in
  `<locale>/firefox-ios.xliff`. Translations go back through the API, and the
  next sync writes them into the repository.
- **Uploads land as *pretranslations*, not approved translations.** Approved
  translations are never overwritten, and anything failing a quality check is
  dropped rather than published. This is a suggestion for the locale team to
  review — say so when you report, and do not describe the locale as
  "completed".

Work happens in a staging tree under `.backfill/<locale>/`, holding a partial
XLIFF with *only* the untranslated units. The upload endpoint is additive, so a
partial file updates only the strings it carries.

Run the scripts in `scripts/` with the repository's virtualenv,
`.venv/bin/python`. They need `moz-l10n` in addition to the automation's own
dependencies; install it with `uv pip install --python .venv/bin/python
moz-l10n` (that venv has no `pip`). It is deliberately **not** in
`.github/scripts/requirements.txt` — that file defines the CI environment and
this skill is a local tool.

All parsing and serialization goes through `moz.l10n`, never by hand:
`parse_resource`/`serialize_resource` round-trip all 103 locale files
byte-for-byte, including `xml:space="preserve"` and the exact `<file>`/`<header>`
shape Pontoon expects. Extend the scripts the same way rather than reaching for
string manipulation or `lxml`.

## What "missing" means here

Every locale file carries **the same trans-unit set as en-US** — the automation
keeps them structurally in sync. So nothing is ever absent: a string is missing
when its `<trans-unit>` has no `<target>`. In the parsed model that is an entry
whose message pattern is empty.

There is one product and one Pontoon resource, `firefox-ios.xliff`, so a whole
backfill is a single upload. The entity key is **two parts**, the `<file
original>` and the unit id, which is why the staged file keeps its `<file>`
grouping — a unit moved into the wrong `<file>` matches nothing in Pontoon.

`en-US` (the reference) and `es` (generated from `es-ES` by `update_es.yml`) are
not Pontoon locales; the script refuses both.

## 1. Survey the gap

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/analyze_locale.py <locale> --report-only
```

Reports untranslated units, broken down by `<file original>`. If the locale has
no directory yet — newly enabled in Pontoon — it says so and stages from en-US
instead, so a brand-new locale backfills like any other.

Report the totals to the user before writing anything. A locale can be missing
well over a thousand strings, so agree on scope first; `--filter <substring>`
narrows to one `.strings` file (for example `--filter Onboarding`).

Then stage it:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/analyze_locale.py <locale>
```

That writes `.backfill/<locale>/` with `staged/firefox-ios.xliff`,
`manifest.json`, `locale.json` and `report.md`. Each staged `<target>` is
seeded with the en-US text, so there is something to overwrite and the
placeholders start out correct.

There are no plurals in this project: iOS plurals live in `.stringsdict` files,
and none are present. If that ever changes, plural units will parse as
`SelectMessage` and this skill will need a plural-category step like the
Android one.

## 2. Build a style guide before translating anything

Do not skip this and do not translate from general knowledge of the language.
The locale team has conventions, and a pretranslation that ignores them is
worse than no pretranslation. Write the findings to
`.backfill/<locale>/style-guide.md` and keep it open while translating.

**Existing translations.** The strongest evidence, because it is this team
translating this product. XLIFF keeps `<source>` next to `<target>`, so the
corpus comes straight out of the locale file:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/dump_pairs.py <locale> --sample 400 --out /tmp/<locale>-pairs.tsv
.venv/bin/python .claude/skills/backfill-locale/scripts/dump_pairs.py <locale> --grep bookmark   # probe a specific term
```

Read the sample and settle at least: how the user is addressed (formal,
informal, impersonal); whether buttons are imperative or infinitive; sentence
vs title case; which quotation marks and apostrophe are used; whether UI nouns
are translated or kept in English; where `%@` sits relative to the words; how
brand names (`Firefox`, `Mozilla`, `Sync`) are treated — normally left
untranslated and never declined.

**Terminology.** Pontoon's approved glossary for the locale:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/fetch_terminology.py <locale> --out /tmp/<locale>-terms.tsv
```

Binding where it applies. When the glossary and the corpus disagree, follow the
corpus and note the conflict — the corpus is what the team actually ships.

**Team documentation.** `.backfill/<locale>/locale.json` carries the team
description from Pontoon, which often links to the team's own style guide. If
it does, read it; it outranks anything you infer.

If a locale has almost no existing translations, say so explicitly: the style
guide rests on the glossary alone and the output deserves closer review.

## 3. Translate the staged file

Edit the `<target>` values in `.backfill/<locale>/staged/firefox-ios.xliff`.
Leave everything else byte-identical — `<source>`, `<note>`, ids, attributes,
the `<file>` grouping, indentation.

The `<note>` is context, not decoration. It is the developer comment: it says
what `%@` will be replaced with, whether the string is a button or an
accessibility label, and how much room there is. Read it before translating.

Mechanical rules:

- Keep every format specifier exactly as-is, same number and same form: `%@`,
  `%1$@`, `%d`, `%1$d`. Reorder them only via their positional index, and if a
  string has more than one they must all stay.
- Write the text as XML: `&amp;`, `&lt;` and `&gt;` where needed. Unlike
  Android, quotes and apostrophes need no backslash escaping — prefer the
  locale's typographic apostrophe where the corpus uses it.
- Leave trailing/leading whitespace and final punctuation as the source has it.
  `xml:space="preserve"` means whitespace is significant.
- Do not translate brand names (`Firefox`, `Focus`, `Klar`, `Pocket`).

A string you genuinely cannot translate — no context, or no confident
rendering — should have its **whole `<trans-unit>` deleted** from the staged
file, not left in English. Uploading English as a pretranslation is the one
outcome to avoid.

## 4. Verify

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/verify_staged.py --manifest .backfill/<locale>/manifest.json
```

It parses the staged file with `moz.l10n` and compares it to en-US as
structured data, so format specifiers are matched exactly rather than by regex:

| check | meaning |
| --- | --- |
| `xml` | the file does not parse |
| `unknown-key` | the unit is not in the en-US reference |
| `missing-target` | the unit has no `<target>`, so it would upload nothing |
| `placeholder` | a format specifier was dropped, added or renumbered |
| `normalization` | re-serializing does not reproduce the file, printed as a diff with `repr` so whitespace differences are visible |
| `untranslated` | the target is still identical to the en-US source |

Everything except `untranslated` blocks the upload and must be fixed. Work
through every `untranslated` line by hand; some are legitimate (a brand name,
`OK`). Translate or delete the rest, then re-run with `--allow-untranslated` to
confirm the file is otherwise clean.

## 5. Upload as pretranslations

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/upload_pretranslations.py \
  --manifest .backfill/<locale>/manifest.json --dry-run
```

The real upload needs a Pontoon Personal Access Token and membership of the
`pretranslators` group. **Ask the user before uploading** — it publishes to
production Pontoon and is visible to the locale team. Never invent a token:

```bash
PONTOON_TOKEN=… .venv/bin/python .claude/skills/backfill-locale/scripts/upload_pretranslations.py \
  --manifest .backfill/<locale>/manifest.json
```

A full-locale backfill is one request, so the rate limit is not a concern here,
but the file must stay under 5000 kB — a complete 1,950-unit locale is around
550 kB, so there is plenty of headroom.

If the upload returns `403`, check the token separately before anything else.
This is read-only and uploads nothing:

```bash
PONTOON_TOKEN=… .venv/bin/python .claude/skills/backfill-locale/scripts/upload_pretranslations.py \
  --manifest .backfill/<locale>/manifest.json --check-auth
```

A PAT is `<id>_<secret>` — digits, an underscore, then an alphanumeric secret —
so it needs no shell quoting. `--check-auth` prints the exact cause, and
distinguishes a bad token from a valid token whose account simply lacks
translator rights or `pretranslators` membership. Note that env vars do not
persist between tool calls, so set `PONTOON_TOKEN` inline on the same command
line as the script.

See `reference/pontoon-api.md` for the endpoint contract and the response
counters.

## 6. Report

Summarize: units staged and per `.strings` file, what the style guide
concluded, which units you deleted rather than guessed, and the upload counters
(`created` / `replaced` / `converted` / `unchanged` / `skipped`, plus any
failed checks). State plainly that these are pretranslations awaiting the
locale team's review.

The staging tree is scratch space — check `.gitignore` covers `.backfill/`
before leaving it. Never commit or push; that is the user's call.
