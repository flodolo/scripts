# en-CA style rules

Derived from a one-time analysis of every `values-en-rCA/strings.xml` in this
repository against its `values/strings.xml` en-US reference (43 file pairs,
2,929 reference entries). At the time of the analysis en-CA had **18 missing
entries, 0 obsolete entries, and 29 entries whose value differed from en-US**.

Of those 29 divergences, **18 are pure Canadian-spelling changes** and are fully
reproduced by the `AUTO_RULES` table in `scripts/backfill_en_ca.py`. The other
11 are documented under [Known divergences](#known-divergences) and are *not*
rules to apply.

## Rule 0 — en-CA is a byte-for-byte mirror of en-US except for string values

This is the single most important finding. After backfilling, every en-CA file
is *structurally identical* to its en-US reference:

- same comments, verbatim, including multi-line comments and section headers
  (`<!-- Home Fragment ... -->`);
- same entry order;
- same attributes, verbatim, including `tools:ignore="UnusedResources"`,
  `tools:ignore="BrandUsage"` and the `xmlns:ns0`/`ns0:ignore` form that the
  upstream extraction tooling sometimes emits;
- same indentation, blank lines, and file header (MPL block);
- same `<plurals>` quantities and `<string-array>` item counts.

Comments are **never** Canadianized — `<!-- ... color scheme ... -->` stays
`color` in en-CA while the string value becomes `colour`. The same holds for
attribute values and for the `License` in the MPL header.

Consequence: a missing entry is backfilled by copying the en-US lines *verbatim*
(comment block included) into the aligned position, then rewriting only the text
between `>` and `<` inside `<string>` / `<item>`.

## Rule 1 — `-or` → `-our`

`color`, `favorite`, `favor(able)`, `behavior(al)`, `neighbor(hood)`, `honor`,
`humor`, `labor`, `rumor`, `savor`, `flavor`, `harbor`, `odor`, `vapor`,
`valor`, `endeavor`, `armor`, `vigor`, `splendor`, `clamor`, `demeanor`,
`parlor`, `candor`, `tumor` — and their inflections.

Corpus evidence: `colour` ×9, `favourite` ×4, `Neighbourhood` ×1. No `-or`
form survives in any en-CA string value.

Exceptions that keep the US `-or` form: `honorary`, `honorarium`, `humorous`,
`rigorous`, `vigorous`, `laborious`.

## Rule 2 — single `-l-` → doubled `-ll-` before a vowel suffix

`canceled`→`cancelled`, `canceling`→`cancelling`, `cancelation`→`cancellation`,
`traveled/traveling/traveler`, `labeled/labeling`, `modeled/modeling`,
`fueled/fueling`, `signaled/signaling`, `totaled/totaling`,
`leveled/leveling`, `dialed/dialing`, `counseled/counseling`, `equaled`,
`marveled`.

Corpus evidence: `cancelled` ×2 against `canceled` ×2 in en-US.
Note the bare stem is unaffected: **`Cancel` stays `Cancel`** (~50 occurrences).

## Rule 3 — `-yze` → `-yse`

`analyze`, `analyzes`, `analyzed`, `analyzing`, `paralyze`, `catalyze`,
`breathalyze`.

Corpus evidence: `analyse` ×1 (`preference_privacy_block_analytics_summary`).

Not affected: `analysis`, `analyst`, **`analytics`** (the string ID
`..._block_analytics_...` and the word "analytics" both keep the `z`-free
US form as-is).

## Rule 4 — `-er` → `-re`

`center`/`centers`/`centered` → `centre`/`centres`/`centred`, `theater`,
`liter`, `fiber`, `caliber`.

No occurrences in the current corpus, so this rule is asserted from Canadian
convention rather than from local evidence. `meter` is deliberately *not*
automatic — see [Review list](#review-list).

## Rule 5 — `gray` → `grey`

Corpus evidence: en-US already ships `Grey` in `tab_group_color_grey`, and
en-CA matches. Also covers `grayed`, `grayscale`.

## Rule 6 — noun `-ense` → `-ence`

`defense`→`defence`, `offense`→`offence`, `pretense`→`pretence`.
`license` is context dependent — see [Review list](#review-list).

## Rule 7 — `-ize` / `-ization` is Canadian; never change it to `-ise`

This is where en-CA and en-GB diverge, and it is the easiest mistake to make.
en-CA keeps every one of these, verified verbatim against en-US:

`customize` ×21, `summarize` ×26, `organization` ×8, `recognize` ×2,
`authorize` ×1 — plus `optimize`, `synchronize`, `personalize`, `prioritize`,
`apologize`, `realize`, `finalize`, `maximize`, `minimize`, `utilize`,
`capitalize`, `customization`, `summarization`.

For contrast, the en-GB files in this repo rewrite all of these
(`summarize`→`summarise`, `Customize`→`Customise`, …). **Do not copy en-GB.**

## Rule 8 — no regionalization beyond spelling

en-CA changes spelling only. Everything en-GB additionally rewrites is left in
its en-US form by en-CA. Verified against `addresses_*` and the wider corpus:

| en-US | en-CA | en-GB (do not copy) |
| --- | --- | --- |
| `State` | `State` | `County` |
| `Zip` | `Zip` | `Postcode` |
| `Postal Code` | `Postal Code` | `Post Code` |
| `Organization` | `Organization` | `Organisation` |
| `website` / `webpage` | unchanged | `web site` / `web page` |
| `Sync`, `synced`, `syncing` | unchanged | `Synchronise`, `synchronised`, … |
| `back` / `forward` | unchanged | `backwards` / `forwards` |
| `cart` | unchanged | `basket` |
| `cellular` | unchanged | `mobile` |

Also kept in the US form: `program` (not `programme`), `aluminum`,
`tire`, `curb`, `check` (verify/checkbox).

## Rule 9 — leave typography, placeholders and markup untouched

Copy verbatim: curly apostrophes (`’`) and quotes (`“ ”`), `%s` / `%1$s` /
`%2$d` placeholders and their order, `\n` escapes and any surrounding
whitespace, inline HTML (`<b>`, `<em>`, `<label>`, `<p>`, `<q>`, `<br>`),
XML entities, and emoji. Date, time and number formats are not localized.

## Review list

The script never applies these automatically; it prints a `! review:` line and
leaves the en-US form in place for a human to resolve.

| Word | Decision |
| --- | --- |
| `license` | noun → `licence`; verb → stays `license`. Never touch the MPL header. |
| `practice` | noun → `practice`; verb → `practise`. |
| `dialog` | UI/technical sense stays `dialog` (matches the corpus: `dialog` ×373 in comments, `dialogue` never used in a value). Conversational sense → `dialogue`. |
| `catalog`, `analog` | generic prose → `catalogue`/`analogue`; keep the US form if it names an API or field. |
| `meter` | unit of length → `metre`; measuring device → `meter`. |
| `enroll`, `fulfill` | Canadian usage is mixed. Prefer `enrol`/`enrolment`, `fulfil`/`fulfilment` for the bare stem; `fulfilled`/`fulfilling` keep the double `l`. |
| `installment` | payment sense → `instalment`. |
| `skillful`, `willful` | → `skilful`, `wilful`. |
| `judgment` | legal sense keeps `judgment`; general prose often `judgement`. Match neighbouring strings. |
| `acknowledgment` | general prose → `acknowledgement`. |
| `AI enhancements`, `AI-powered features` | existing en-CA strings say `features with AI`. Reuse only if it reads naturally; otherwise keep the en-US phrasing. See below. |

## Known divergences

The 11 en-CA/en-US value differences that are *not* spelling rules. They are
pre-existing translations: leave them exactly as they are, and do not treat
them as precedent for new strings.

1. **`ai_controls_*` (6 strings, fenix)** — en-CA renders "AI enhancements" /
   "AI-powered features" as "features with AI". This wording never appeared in
   en-US and en-GB does not use it, so it is an en-CA translator choice (landed
   via Pontoon in `a39c783def`). Surfaced as a review flag, not a rule.
2. **`tip_*` (4 strings, focus-android)** — en-CA drops the space after `\n`
   that en-US has (`?\n Try` → `?\nTry`). A whitespace cleanup, not a style
   rule. New strings should keep en-US whitespace verbatim.
3. **`mozac_browser_errorpages_security_bad_hsts_cert_techInfo2`** — en-CA
   trims the spaces just inside `<label> … </label>`. Same story.

## Scope

- Backfill applies to `mozilla-mobile/**/values-en-rCA/*.xml` only. Every one
  of the 43 files has an en-US reference at the same path with `values-en-rCA`
  replaced by `values`.
- Obsolete entries (in en-CA, absent from en-US) are reported and **kept**.
- Existing en-CA translations are never modified.
