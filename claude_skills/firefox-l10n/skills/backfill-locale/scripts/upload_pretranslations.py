#!/usr/bin/env python3
"""Upload staged files to Pontoon as pretranslations.

Posts each file in a manifest to `POST /api/v2/upload/pretranslations/`, which
stores the translations as pretranslations rather than approved translations:
approved translations are never overwritten, a matching suggestion is promoted
keeping its original author, and anything failing a quality check is skipped.

The endpoint is additive, so the partial files written by `analyze_locale.py`
update only the strings they contain.

Requires a Pontoon Personal Access Token (https://pontoon.mozilla.org/settings/)
from the `PONTOON_TOKEN` environment variable or --token, and membership of the
`pretranslators` group on top of translator rights for the locale.

Usage:
    PONTOON_TOKEN=... upload_pretranslations.py --manifest .backfill/it/manifest.json
    upload_pretranslations.py --manifest ... --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import requests

DEFAULT_URL = "https://pontoon.mozilla.org/api/v2/upload/pretranslations/"
CHECK_URL = "https://pontoon.mozilla.org/api/v2/projects/{project}/?fields=slug"

# Pontoon rejects a bad token before any permission check, with a distinct
# message per cause. Mapping them saves guessing at a bare 403.
TOKEN_HINTS = {
    "Authentication credentials were not provided.": (
        "the Authorization header never reached the server -- PONTOON_TOKEN was "
        "empty or never exported into this process"
    ),
    "Malformed token format.": (
        "the header arrived, but the token is not `<id>_<secret>` -- it was "
        "truncated or mangled on the way, e.g. by shell quoting"
    ),
    "Invalid token.": "well-formed, but no token matches it; check for a typo",
    "Token has been revoked.": "create a new token in Pontoon settings",
    "Token has expired.": "PATs expire one year after creation; create a new one",
    "User is disabled.": "the account behind the token is disabled",
}

# Server-side limits: 30 calls/minute burst, 180 calls/hour sustained. Calls
# rejected with 429 still count against the hourly quota, so it is much cheaper
# to pace requests than to retry into the limit.
MIN_INTERVAL = 2.5
MAX_BYTES = 5000 * 1024

SUMMARY_KEYS = ["created", "replaced", "converted", "unchanged", "skipped"]


def check_auth(session, project, timeout) -> int:
    """Validate the token with a read-only request that writes nothing.

    Pontoon authenticates a PAT on every endpoint, including public GETs, so
    this separates "the token is wrong" from "the token is fine but the account
    lacks permission" -- which both surface as a bare 403 on the upload itself.
    """
    resp = session.get(CHECK_URL.format(project=project), timeout=timeout)
    if resp.status_code == 200:
        print(f"token OK: authenticated, and {project} is visible.")
        print(
            "If the upload still returns 403, the token is not the problem: the "
            "account lacks translator rights for the locale, or is not in the "
            "`pretranslators` group."
        )
        return 0
    try:
        detail = resp.json().get("detail", resp.text[:200])
    except ValueError:
        detail = resp.text[:200]
    print(f"token REJECTED: HTTP {resp.status_code} {detail}")
    hint = TOKEN_HINTS.get(detail)
    if hint:
        print(f"  -> {hint}")
    return 1


def upload(session, url, project, locale, resource, path, timeout):
    with open(path, "rb") as fh:
        files = {"uploadfile": (os.path.basename(path), fh, "application/xml")}
        data = {"project": project, "locale": locale, "resource": resource}
        return session.post(url, data=data, files=files, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--manifest", required=True, help="manifest.json from analyze_locale.py"
    )
    ap.add_argument("--token", default=os.environ.get("PONTOON_TOKEN"))
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--locale", help="override the manifest's locale")
    ap.add_argument("--project", help="override the manifest's project slug")
    ap.add_argument("--filter", help="only resources whose path contains this")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be posted, post nothing",
    )
    ap.add_argument(
        "--check-auth",
        action="store_true",
        help="validate the token with a read-only request, then exit",
    )
    args = ap.parse_args()

    manifest_path = os.path.abspath(args.manifest)
    base = os.path.dirname(manifest_path)
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    locale = args.locale or manifest["locale"]
    project = args.project or manifest["project"]
    entries = [
        e for e in manifest["files"] if not args.filter or args.filter in e["resource"]
    ]

    if not args.dry_run and not args.token:
        print("ERROR: no token. Set PONTOON_TOKEN or pass --token.", file=sys.stderr)
        return 2

    session = requests.Session()
    if args.token:
        token = args.token.strip()
        if token != args.token:
            print("note: stripped surrounding whitespace from the token")
        session.headers["Authorization"] = f"Bearer {token}"

    if args.check_auth:
        return check_auth(session, project, args.timeout)

    if not entries:
        print("nothing to upload")
        return 0

    totals = dict.fromkeys(SUMMARY_KEYS, 0)
    failures = []
    last_call = 0.0

    for i, entry in enumerate(entries, 1):
        path = os.path.join(base, entry["file"])
        resource = entry["resource"]
        size = os.path.getsize(path)
        prefix = f"[{i}/{len(entries)}] {resource}"

        if size > MAX_BYTES:
            print(f"{prefix}: SKIP, {size} bytes exceeds the 5000 kB limit")
            failures.append((resource, "file too large"))
            continue
        if args.dry_run:
            print(f"{prefix}: would post {entry['entries']} entries ({size} bytes)")
            continue

        wait = MIN_INTERVAL - (time.monotonic() - last_call)
        if wait > 0:
            time.sleep(wait)

        for attempt in range(4):
            resp = upload(
                session, args.url, project, locale, resource, path, args.timeout
            )
            last_call = time.monotonic()
            if resp.status_code != 429:
                break
            backoff = int(resp.headers.get("Retry-After", 0)) or 60 * (attempt + 1)
            print(f"{prefix}: rate limited, waiting {backoff}s")
            time.sleep(backoff)

        if resp.status_code != 200:
            print(f"{prefix}: HTTP {resp.status_code} {resp.text[:300]}")
            failures.append((resource, f"HTTP {resp.status_code}"))
            continue

        result = resp.json()
        for key in SUMMARY_KEYS:
            totals[key] += result.get(key, 0)
        counts = " ".join(f"{k}={result.get(k, 0)}" for k in SUMMARY_KEYS)
        print(f"{prefix}: {counts}")
        for check in result.get("failed_checks", []):
            print(f"    failed check {check.get('key')}: {check.get('errors')}")
        if result.get("undefined_keys_count"):
            print(f"    undefined keys: {result['undefined_keys_count']}")

    print("\n--- totals ---")
    if args.dry_run:
        print(f"{len(entries)} files, {sum(e['entries'] for e in entries)} entries")
        return 0
    for key in SUMMARY_KEYS:
        print(f"{key:<10} {totals[key]}")
    if failures:
        print(f"\n{len(failures)} file(s) failed:")
        for resource, why in failures:
            print(f"  {resource}: {why}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
