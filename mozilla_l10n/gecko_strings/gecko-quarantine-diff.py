#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument(
    "quarantine_path", help="Path to local clone of gecko-strings-quarantine"
)
args = parser.parse_args()

path = args.quarantine_path
if not os.path.isdir(path):
    sys.exit("The folder does not exist")

geckostrings_rev = (
    subprocess.run(
        ["hg", "id", "https://hg.mozilla.org/l10n/gecko-strings"],
        stdout=subprocess.PIPE,
    )
    .stdout.decode("utf-8")
    .strip()
)
print(f"gecko-strings remote tip: {geckostrings_rev}")

quarantine_rev = (
    subprocess.run(
        ["hg", "id", "https://hg.mozilla.org/l10n/gecko-strings-quarantine"],
        stdout=subprocess.PIPE,
    )
    .stdout.decode("utf-8")
    .strip()
)
print(f"quarantine remote tip: {quarantine_rev}")

if geckostrings_rev == quarantine_rev:
    sys.exit("The two repositories have the same tip.")

diff = subprocess.run(
    [
        "hg",
        "diff",
        "--cwd",
        path,
        "-r",
        f"{geckostrings_rev}:{quarantine_rev}",
    ],
    stdout=subprocess.PIPE,
).stdout.decode("utf-8")

for line in diff.split("\n"):
    # Ignore unchanged lines
    if not line.startswith(("+", "-")):
        continue

    if line.startswith("+"):
        if not line.startswith("+++"):
            line = f"\033[92m{line}\x1b[0m"
    elif line.startswith("-"):
        if line.startswith("---"):
            line = f"\n\033[91m{line}\x1b[0m"
        else:
            line = f"\033[91m{line}\x1b[0m"
    print(line)
