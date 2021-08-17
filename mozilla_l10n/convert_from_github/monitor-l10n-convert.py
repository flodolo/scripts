#!/usr/bin/env python3

# Example:
# ./monitor-l10n-convert.py ~/github/blurts-addon/ ~/mozilla/mercurial/l10n_clones/locales
# Add --push to push to remote repository

import argparse
from concurrent import futures
import json
import os
import subprocess
import sys
from tempfile import mkstemp

parser = argparse.ArgumentParser()
parser.add_argument("--method", choices=["rebase", "merge"], default="rebase")
parser.add_argument("--push", action="store_true", help="push results upstream")
parser.add_argument("-p", default=4, metavar="N", help="Run N parallel jobs")
parser.add_argument("project_path", metavar="blurts-addon")
parser.add_argument("l10n_path", metavar="l10n-central")
args = parser.parse_args()


def hg_pull(repo):
    return subprocess.run(
        ["hg", "--cwd", repo, "pull", "-u"], stdout=subprocess.PIPE
    ).stdout.decode("utf-8")


def git_pull(repo):
    return subprocess.run(
        ["git", "pull"], cwd=repo, stdout=subprocess.PIPE
    ).stdout.decode("utf-8")


def migrate(locale):
    branchmap = os.path.join(os.path.dirname(__file__), "monitor_branchmap")
    monitor_locale = locale
    # Special case ja-JP-mac (we need to read 'ja')
    if locale == "ja-JP-mac":
        monitor_locale = "ja"
    locale = locale.replace("_", "-")
    repo = os.path.join(args.l10n_path, locale)
    out = ""
    out += "starting migration for {}\n".format(locale)
    if args.method == "rebase":
        out += hg_pull(repo)
    fd, filemap = mkstemp(text=True)
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(
                """\
    include "src/locales/{loc}/strings.properties"
    rename "src/locales/{loc}/strings.properties" "browser/extensions/fxmonitor/fxmonitor.properties"
    """.format(
                    loc=monitor_locale
                )
            )
        shamap = os.path.join(args.l10n_path, locale, ".hg", "shamap")
        if os.path.isfile(shamap):
            os.remove(shamap)
        if args.method == "rebase":
            content = subprocess.run(
                [
                    "hg",
                    "log",
                    "-r",
                    "default",
                    "-T17f285deb7c13e534c6656fb1c3e28026a3dccaa {node}\n",
                ],
                cwd=repo,
                stdout=subprocess.PIPE,
            ).stdout.decode("utf-8")
            with open(shamap, "w") as fh:
                fh.write(content)
        # ignore all the commit messages in each locale, don't add to output
        subprocess.run(
            [
                "hg",
                "convert",
                "-r",
                "l10n",
                "--branchmap",
                branchmap,
                "--filemap",
                filemap,
                args.project_path,
                repo,
            ],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        if args.method == "merge":
            out += hg_pull(repo)
            heads = json.loads(
                subprocess.run(
                    ["hg", "heads", "-Tjson", "default"],
                    cwd=repo,
                    stdout=subprocess.PIPE,
                ).stdout
            )
            if len(heads) == 2:
                out += subprocess.run(
                    ["hg", "up", "-r", heads[0]["node"]],
                    cwd=repo,
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")
                out += subprocess.run(
                    ["hg", "merge", heads[1]["node"]], cwd=repo, stdout=subprocess.PIPE
                ).stdout.decode("utf-8")
                out += subprocess.run(
                    [
                        "hg",
                        "ci",
                        "-m",
                        "Merging localization of Firefox Monitor Add-on",
                    ],
                    cwd=repo,
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")
        if args.push:
            out += subprocess.run(
                ["hg", "push", "-r", "default"], cwd=repo, stdout=subprocess.PIPE
            ).stdout.decode("utf-8")
            # Pull again
            out += hg_pull(repo)
    finally:
        os.remove(filemap)
    out += "finished migration for {}\n".format(locale)
    return out


sys.stdout.write(git_pull(args.project_path))
locales = [
    dir
    for dir in os.listdir(os.path.join(args.project_path, "src/locales"))
    if dir != "en-US" and not dir.startswith(".")
]
# Add ja-JP-mac
locales.append("ja-JP-mac")
locales.sort()

# Limit to one locale for testing
# locales = ['it']

handle = []
skip = []
for loc in locales:
    gecko_loc = loc.replace("_", "-")
    if os.path.isdir(os.path.join(args.l10n_path, gecko_loc)):
        handle.append(loc)
    else:
        skip.append(loc)

with futures.ThreadPoolExecutor(max_workers=args.p) as executor:
    for stdout in executor.map(migrate, handle):
        sys.stdout.write(stdout)

if skip:
    print("Skipped these locales: " + ", ".join(skip))
