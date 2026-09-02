# How the en-CA rules were derived (2026-08-25)

One-time analysis of `firefox-l10n/en-CA` against
`~/mozilla-source/git/firefox-quarantine` (en-US), using `moz.l10n` to parse every
`.ftl`, `.properties` and `.ini` file into `(file, key, attribute, variant)`
→ text, including Fluent attributes and every select variant.

## Corpus

| | count |
|---|---|
| en-US strings (values + attributes + variants) | 20,494 |
| present in en-CA | 20,392 |
| byte-identical to en-US | 19,951 (97.8%) |
| differing | 441 (2.2%) |
| missing | 102 units = **77 entries in 13 files** |
| files only in en-US | `toolkit/services/aboutSyncLog.ftl`, `toolkit/toolkit/pdfviewer/embedFallback.ftl` |

The 441 differences were word-diffed and clustered; every cluster with more
than one occurrence became a rule in `style-rules.md`. No `-ise`, no British
`programme`/`catalogue`/`cheque`/`tyre`/`storey` forms appear anywhere, which
is what pins down the "Canadian, not British" character of the locale.

## Rule validation

`ca_adapt.py` was run over all 20,392 shared strings and its output compared
with the real en-CA translation:

**20,240 / 20,392 (99.25%) reproduced exactly.**

The 152 residual mismatches are all known-inconsistent or judgement cases:

| kind | count | handling |
|---|---|---|
| legacy `‘…’` quotes en-CA never converted | ~40 | rule says convert; `check_style.py --quotes` lists them |
| access key / shortcut letters that differ from en-US in case only | ~45 | no rule; never churn existing entries |
| `Cert` → `Certificate` | 8 | emitted as a warning, applied by hand |
| one-off editorial fixes (`sssssh`, `read`→`scan`, `Login`→`Log in`) | ~10 | judgement, not automatable |
| pre-existing en-CA typos (`“!“`, double space in `rights-locationawarebrowsing`) | 3 | left alone |

## Checker baseline

`check_style.py` over the whole en-CA tree reports **2 problems**, both a
pre-existing double space in `toolkit/toolkit/about/aboutRights.ftl`
(`rights-locationawarebrowsing`). With `--quotes` it additionally lists the
~40 legacy single-quote strings. Anything beyond that baseline was introduced
by the current change.
