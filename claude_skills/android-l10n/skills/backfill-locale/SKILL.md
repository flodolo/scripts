---
name: backfill-locale
description: Translate the strings a locale is missing in this repository — including whole files the locale does not have yet — and upload them to Pontoon as pretranslations. Use when asked to backfill, complete, fill in, or pretranslate a locale (e.g. "backfill it", "complete the missing Italian strings", "pretranslate fr"), or to report how complete a locale is against the en-US reference.
---

# Backfill a locale

Fill the gap between a locale and the en-US reference in `values/strings.xml`,
then publish the result through Pontoon's pretranslation API.

Two things shape the whole workflow:

- **The locale files in this repository are written by Pontoon's sync** (see the
  `Pontoon/Firefox for Android: Update …` commits). Never hand-edit
  `values-*/strings.xml`. Translations go back through the API, and the next
  sync writes them into the repository.
- **Uploads land as *pretranslations*, not approved translations.** Approved
  translations are never overwritten, and anything failing a quality check is
  dropped rather than published. This is a suggestion for the locale team to
  review — say so when you report, and do not describe the locale as
  "completed".

Work happens in a staging tree under `.backfill/<locale>/`, which holds partial
`strings.xml` files containing *only* the missing entries. The upload endpoint
is additive, so a partial file updates only the strings it carries.

All scripts live in `scripts/` next to this file and take `--config
firefox.toml` (default, → Pontoon project `firefox-for-android`) or `--config
focus.toml` (→ `focus-for-android`). Run them with the repository's virtualenv,
`.venv/bin/python`, which has `moz.l10n` and `requests`.

They do all parsing, serialization and locale-code mapping through `moz.l10n`,
never by hand: `parse_resource`/`serialize_resource` round-trip these files
byte-for-byte, `L10nConfigPaths` resolves the reference/target pairs from the
l10n.toml, and `get_android_locale` maps the locale code to its resource
directory. Extend the scripts the same way rather than reaching for string
manipulation.

## 1. Survey the gap

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/analyze_locale.py <locale> --report-only
```

This resolves every reference file from the project's `l10n.toml` and maps the
locale to its Android resource directory (`en-CA` → `values-en-rCA`, and the
legacy `he` → `iw`, `id` → `in`, `yi` → `ji`), then reports missing entries per
file. Files the locale does not have at all are flagged `NEW` — those are not an
error, just a resource nobody has started.

Report the totals to the user before writing anything. If the number is large,
agree on a scope (`--filter <path substring>` narrows to one component or app).

Then stage it:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/analyze_locale.py <locale>
```

That writes `.backfill/<locale>/` with `staged/` (partial files, values still in
English), `manifest.json`, `locale.json` and `report.md`.

`<plurals>` are rewritten to the locale's own CLDR categories, taken from
Pontoon's `cldr_plurals` for the locale. English has only `one`/`other`; a
locale with `few`/`many` gets an `<item>` per category, each seeded with the
English `other` form. Every seeded category needs a genuinely different form —
that is the point of the category. Use Pontoon's set exactly as given, even
where it is narrower than full CLDR (Russian is `one, few, many`, with no
`other`): that is the set the Pontoon entity has, and the upload target.

## 2. Build a style guide before translating anything

Do not skip this and do not translate from general knowledge of the language.
The locale team has conventions, and a pretranslation that ignores them is
worse than no pretranslation. Write the findings to
`.backfill/<locale>/style-guide.md` and keep it open while translating.

**Existing translations.** This is the strongest evidence, because it is this
team translating these products:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/dump_pairs.py <locale> --sample 400 --out /tmp/<locale>-pairs.tsv
.venv/bin/python .claude/skills/backfill-locale/scripts/dump_pairs.py <locale> --grep bookmark   # probe a specific term
```

Read the sample and settle at least: how the user is addressed (formal,
informal, impersonal); whether buttons are imperative or infinitive; sentence
vs title case; which quotation marks and apostrophe are used; whether UI nouns
are translated or kept in English; how placeholders and `<xliff:g>` are
positioned; how brand names (`Firefox`, `Mozilla`, `Sync`) are treated —
normally left untranslated and never declined. Probe with `--grep` for any term
you are unsure about, and prefer an existing rendering over a new one.

**Terminology.** Pontoon's approved glossary for the locale:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/fetch_terminology.py <locale> --out /tmp/<locale>-terms.tsv
```

These translations are binding where they apply. When the glossary and the
existing corpus disagree, follow the corpus and note the conflict in the style
guide — the corpus is what the team actually ships.

**Team documentation.** `.backfill/<locale>/locale.json` carries the team
description from Pontoon, which often links to the team's own style guide. If it
does, read it; it outranks anything you infer.

If a locale has almost no existing translations, say so explicitly: the style
guide rests on the glossary alone and the output deserves closer review.

## 3. Translate the staged files

Edit the values in `.backfill/<locale>/staged/**/strings.xml` in place. Leave
everything else byte-identical — comments, keys, attributes, indentation, entry
order.

The developer comment above each string is context, not decoration. It tells you
what `%1$s` will be replaced with, whether the string is a button or a screen
reader announcement, and how much room there is. Read it before translating.

Mechanical rules that Pontoon's quality checks enforce:

- Keep every placeholder exactly as-is, same number and same form: `%s`,
  `%1$s`, `%2$,d`. Reorder them only via their positional index, and if a string
  has more than one placeholder they must all stay.
- Keep `<xliff:g>` tags and their attributes intact around the text they wrap.
- Escape `'` as `\'` and `"` as `\"`. An unescaped apostrophe is merely wrong,
  but an unescaped double quote is *lossy*: Android reads it as a
  whitespace-preservation delimiter and drops it, so `pini "ni"` silently
  becomes `pini ni`. Step 4 catches both. Prefer the locale's typographic
  apostrophe (e.g. `’`) where the corpus uses it — it needs no escaping.
- Leave trailing/leading whitespace and final punctuation as the source has it.
- Do not translate brand names, or anything the comment marks as hardcoded
  (`tools:ignore="BrandUsage"`).

A string you genuinely cannot translate — no context, or no confident
rendering — should be **deleted from the staged file**, not left in English.
Uploading English as a pretranslation for the locale is the one outcome to
avoid.

## 4. Verify

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/verify_staged.py --manifest .backfill/<locale>/manifest.json
```

It parses each staged file with `moz.l10n` and compares it to the reference as
structured data, so placeholders are matched exactly (per plural form, not in
aggregate) rather than by regex. It reports:

| check | meaning |
| --- | --- |
| `xml` | the file does not parse |
| `unknown-key` | the entry is not in the reference |
| `placeholder` | a placeholder was dropped, added or renumbered |
| `plural` | the plural categories do not match the locale's set |
| `normalization` | re-serializing does not reproduce the file, printed as a diff — this is how a bad escape shows up, including a swallowed `"` |
| `untranslated` | the value is still identical to en-US |

Everything except `untranslated` blocks the upload and must be fixed. Read a
`normalization` diff carefully: the `-` line is what you wrote and the `+` line
is what Android would actually read.

Work through every `untranslated` line by hand. Some are legitimate (a brand
name, `OK`); translate or delete the rest. Only once you have reviewed them all,
re-run with `--allow-untranslated` to confirm the file is otherwise clean.

## 5. Upload as pretranslations

The manifest is the list of files to upload. Check it first:

```bash
.venv/bin/python .claude/skills/backfill-locale/scripts/upload_pretranslations.py \
  --manifest .backfill/<locale>/manifest.json --dry-run
```

The real upload needs a Pontoon Personal Access Token and membership of the
`pretranslators` group. **Ask the user before uploading** — it publishes to
production Pontoon and is visible to the locale team. Never invent a token, and
do not put one on the command line if it can be avoided:

```bash
PONTOON_TOKEN=… .venv/bin/python .claude/skills/backfill-locale/scripts/upload_pretranslations.py \
  --manifest .backfill/<locale>/manifest.json
```

The script paces itself under Pontoon's rate limit (30 calls/minute, 180/hour)
and backs off on `429`. Do not run it in parallel or loop it on failure —
rejected calls still consume the hourly quota.

If the upload returns `403`, check the token separately before touching
anything else. This is read-only and uploads nothing:

```bash
PONTOON_TOKEN=… .venv/bin/python .claude/skills/backfill-locale/scripts/upload_pretranslations.py \
  --manifest .backfill/<locale>/manifest.json --check-auth
```

A PAT is `<id>_<secret>` — digits, an underscore, then an alphanumeric secret —
so it needs no shell quoting. Pontoon names each failure distinctly, and
`--check-auth` prints the cause:

| response | meaning |
| --- | --- |
| `token OK` | the token authenticates; a `403` on upload is then a *permission* problem — no translator rights for the locale, or not in the `pretranslators` group |
| `Authentication credentials were not provided.` | no `Authorization` header arrived: `PONTOON_TOKEN` was empty or never reached the process |
| `Malformed token format.` | the header arrived but the value is not `<id>_<secret>`: truncated or mangled |
| `Invalid token.` | well formed, but no such token — a typo |
| `Token has been revoked.` / `Token has expired.` | make a new one; PATs last a year |

Note that env vars do not persist between tool calls, so `export PONTOON_TOKEN=…`
in one command is gone by the next. Always set it inline on the same command
line as the script.

See `reference/pontoon-api.md` for the endpoint contract and what each counter
in the response means.

## 6. Report

Summarize: entries staged per file, how many files were new for the locale, what
the style guide concluded, which strings you deleted rather than guessed, and
the upload counters (`created` / `replaced` / `converted` / `unchanged` /
`skipped`, plus any failed checks). State plainly that these are pretranslations
awaiting the locale team's review.

The staging tree is scratch space; `.gitignore` already excludes it via `.*`.
Leave it for the user to inspect. Never commit or push; that is the user's call.
