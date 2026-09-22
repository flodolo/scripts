# Pontoon API notes for this skill

Source: <https://github.com/mozilla/pontoon/blob/main/pontoon/api/README.md>.
Verified against production Pontoon in September 2026.

## Resource path and entity keys

This repository is one Pontoon project, `firefox-for-ios`, with a **single
resource**: `firefox-ios.xliff`. Its format is `xcode`.

An entity key has **two parts**: the `<file original>` and the `<trans-unit>`
id. Confirmed with:

```bash
curl -s "https://pontoon.mozilla.org/api/v2/entities/firefox-for-ios/firefox-ios.xliff/App%20Icon/"
```

which returns
`"key": ["Client/en-US.lproj/InfoPlist.strings", "App Icon"]`,
`"resource": {"path": "firefox-ios.xliff", "format": "xcode"}`.

That two-part key is why a staged partial file must keep its `<file>`
grouping: the same unit id under a different `original` is a different entity,
and would land in `undefined_keys`.

Locale codes need no mapping — the Pontoon locale code is the directory name.
(`locale_config.PONTOON_TO_IOS` maps to the *product* codes used in the app
repo's `.lproj` folders, which is a different thing and not used here.)

## `POST /api/v2/upload/pretranslations/`

`multipart/form-data` with `project`, `locale`, `resource`, `uploadfile`.
Authenticate with `Authorization: Bearer <PAT>`; tokens come from
<https://pontoon.mozilla.org/settings/> and expire after a year. Requires
membership of the `pretranslators` group **in addition to** translator rights
for the locale and project.

The upload is additive: strings absent from the file are left untouched, so
partial files are the intended way to update a subset.

Response counters:

| Field | Meaning |
| --- | --- |
| `created` | pretranslation added where there was none |
| `replaced` | replaced a different pretranslation or fuzzy translation; the old one is rejected |
| `converted` | an existing translation matched the upload and became the active pretranslation, keeping its original author |
| `unchanged` | identical to the current pretranslation, ignored |
| `skipped` | left alone because the string is already approved, or was marked fuzzy in the upload |
| `failed_checks` | per-key `errors`/`warnings` from quality checks; those strings were not written (first 100) |
| `undefined_keys` | keys with no matching string in Pontoon, ignored (first 100) |

Approved translations are never touched.

Status codes: `400` invalid field / unparseable or empty file / over 5000 kB ·
`403` bad token or insufficient permission · `404` unknown project, locale or
resource, or resource not enabled for the locale · `409` concurrent change,
retry · `429` rate limited.

## Token format and auth errors

A PAT is `<id>_<secret>`: `PersonalAccessTokenAuthentication` splits the Bearer
value on `_` and casts the first half to `int`. Both halves are alphanumeric,
so the token never needs shell quoting.

Authentication runs on *every* endpoint, including public GETs, which is what
makes `--check-auth` possible: a read-only `GET /api/v2/projects/<slug>/` with a
bad token still returns the same 403 detail as an upload would, without writing
anything.

The membership check is separate and later: `IsPretranslator` requires the
account to be in the `pretranslators` group, and only guards the upload
endpoint. So a token that passes `--check-auth` can still be refused by the
upload — that is a permission problem, not a token problem.

Details, in the order the server checks them: `Authentication credentials were
not provided.` (no Bearer header) · `Malformed token format.` (not
`<id>_<secret>`) · `Invalid token.` (no match) · `Token has been revoked.` ·
`Token has expired.` · `User is disabled.`

## Rate limits

30 calls per minute (burst) and 180 per hour (sustained). With a single
resource a whole backfill is one call, so this rarely bites here. The two are **not
independent**: calls rejected by the burst limit still count against the hourly
quota, so retrying into a `429` can exhaust the hour. `upload_pretranslations.py`
paces requests at one every 2.5s and honours `Retry-After`.

## Other endpoints used

- `GET /api/v2/locales/<code>/` — `cldr_plurals` (comma-separated CLDR indices,
  `0=zero 1=one 2=two 3=few 4=many 5=other`), `direction`, `script`, and
  `team_description`, which often links to the team's own style guide.
- `GET /terminology/<code>.tbx` — the locale's approved glossary as TBX.

## Why `moz.l10n` and not lxml

`parse_resource` / `serialize_resource` round-trip all 103 locale
`firefox-ios.xliff` files byte-for-byte, including the `xml:space="preserve"`
attributes and the `<file>`/`<header>` shape the automation is careful to
preserve. That makes the parsed model safe to build staged files from, and
makes a round-trip difference a reliable signal that hand-edited text is not
what the parser actually sees.

The model maps onto XLIFF cleanly: one `Section` per `<file>` (`section.id` is
the `original`), one `Entry` per `<trans-unit>`, `entry.value` is the
`<target>`, `entry.meta["source"]` the English, `entry.comment` the `<note>`.
**An empty message pattern means there is no `<target>` at all** — that is how
an untranslated string is detected. Format specifiers arrive as `Expression`s
with their original spelling in `attributes["source"]`, so `%1$@` can be
compared exactly rather than by regex.

No unit in this project parses as a `SelectMessage`: iOS plurals live in
`.stringsdict`, and none are present.
