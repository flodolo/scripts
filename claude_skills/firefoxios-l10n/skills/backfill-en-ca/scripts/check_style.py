#! /usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Check en-CA targets against the style rules of the backfill-en-ca skill.

Reports placeholder mismatches, typography drift, American -our/-re spellings
left in place, and -ise/-yse forms that should have stayed -ize/-yze. Exits
non-zero if anything was reported.
"""

import argparse
import re

from xliff_common import index, parse

PLACEHOLDER = re.compile(r"%(?:\d+\$)?[@a-zA-Z]")

# Must be Canadianized in the target (R2, R3).
AMERICAN = [
    "color",
    "favorite",
    "favor",
    "neighborhood",
    "behavior",
    "honor",
    "labor",
    "flavor",
    "humor",
    "rumor",
    "odor",
    "vapor",
    "savor",
    "endeavor",
    "center",
    "theater",
    "fiber",
    "liter",
]
# Short forms that legitimately stay American (R2 exception, R5).
AMERICAN_OK = re.compile(
    r"humorous|coloration|honorary|laborious|meter|license|licens|install|"
    r"practice|program|check|tire|defense|offense|dialog|catalog",
    re.IGNORECASE,
)
# Must NOT be introduced (R4).
OVERCORRECTED = re.compile(
    r"\b\w*(?:ise|ised|ises|ising|isation|yse|ysed|yses|ysing)\b|"
    r"\blicence|\bpractise|\bprogramme|\bcheque\b",
    re.IGNORECASE,
)
ISE_ALLOWED = re.compile(
    r"^(?:wise|rise|risen|rises|rising|noise|noises|else|advise|advised|advises|"
    r"advising|promise|promises|promised|promising|precise|concise|surprise|"
    r"surprised|surprising|paradise|otherwise|likewise|revise|revised|arise|"
    r"arises|arising|raise|raised|raises|raising|praise|wise|expertise|"
    r"franchise|merchandise|exercise|exercised|exercises|exercising|comprise|"
    r"comprises|premise|premises|these|those|use|used|uses|using|because|"
    r"license|licenses|licensed|licensing|clockwise|counterclockwise|paise|"
    r"sunrise|sunrises|disguise|disguised|guise|anise|treatise|demise|devise|"
    r"devised|despise|excise|incise|revise|revises|revising|supervise|"
    r"supervised|improvise|chastise|enterprise|enterprises|paradise)$",
    re.IGNORECASE,
)
TYPOGRAPHY = ["’", "‘", "“", "”", "…", "—", "–", " ", " "]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale", default="en-CA")
    parser.add_argument("--reference", default="en-US")
    args = parser.parse_args()

    reference = index(parse(args.reference))
    locale = index(parse(args.locale))

    problems = []

    def report(key, message):
        problems.append(f"{key[0]}:{key[1]}\n    {message}")

    for key, (source, target) in sorted(locale.items()):
        if target is None:
            continue
        if key not in reference:
            continue

        src_ph = PLACEHOLDER.findall(source or "")
        tgt_ph = PLACEHOLDER.findall(target)
        if src_ph != tgt_ph:
            report(key, f"placeholders: source {src_ph} != target {tgt_ph}")

        for char in TYPOGRAPHY:
            if (source or "").count(char) != target.count(char):
                report(
                    key,
                    f"typography: {char!r} appears "
                    f"{(source or '').count(char)}x in source, "
                    f"{target.count(char)}x in target",
                )

        for word in AMERICAN:
            for match in re.finditer(rf"\b{word}\w*", target, re.IGNORECASE):
                if not AMERICAN_OK.match(match.group(0)):
                    report(key, f"American spelling left in target: {match.group(0)}")

        for match in OVERCORRECTED.finditer(target):
            if not ISE_ALLOWED.match(match.group(0)):
                report(key, f"over-corrected to British form: {match.group(0)}")

        if source is not None and source != target and source.strip() == target.strip():
            report(key, "differs from source only by leading/trailing whitespace")

    for problem in problems:
        print(problem)
    print(f"\n{len(problems)} issue(s) reported for {args.locale}.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
