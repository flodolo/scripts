#!/usr/bin/env python3

# Example:
# ./screenshots-monorepo-convert.py ~/github/screenshots-hg/ ~/mozilla/mercurial/l10n_clones/locales
# Add --push to push to remote repository

import argparse
from concurrent import futures
import json
import os
import subprocess
import sys
from tempfile import mkstemp
from functools import partial

# Relative path to locales folder in the GitHub project
gh_path_locales = 'locales'
# Filename in GitHub
gh_filename = 'screenshots.ftl'
# Full path and filename in Mercurial l10n repository
hg_file = 'browser/browser/screenshots.ftl'
# Initial changeset for rebase. To get this, run in the GitHub repository:
# hg log -r : -l 1 -T"{node}"
initial_changeset = '3fb30a9f2505b9ffb5bb1add96c19fe3bb258820'


def hg_pull(repo):
    return subprocess.run(
        ['hg', '--cwd', repo, 'pull', '-u'],
        stdout=subprocess.PIPE).stdout.decode('utf-8')


def migrate(project_locale, args):
    hg_locale = project_locale
    # Special case ja-JP-mac (we need to read 'ja')
    if project_locale == 'ja-JP-mac':
        hg_locale = 'ja'

    repo = os.path.join(args.l10n_path, hg_locale)
    out = ''
    out += 'Starting migration for {}\n'.format(hg_locale)
    out += hg_pull(repo)

    fd, filemap = mkstemp(text=True)
    try:
        with os.fdopen(fd, 'w') as fh:
            fh.write('''\
    include "{gh_path}/{locale}/{gh_filename}"
    rename "{gh_path}/{locale}/{gh_filename}" "{hg_file}"
    '''.format(
            gh_path=gh_path_locales,
            locale=project_locale,
            gh_filename=gh_filename,
            hg_file=hg_file
        ))

        shamap = os.path.join(args.l10n_path, hg_locale, '.hg', 'shamap')
        if os.path.isfile(shamap):
            os.remove(shamap)

        content = subprocess.run(
            [
                'hg', 'log', '-r', 'default',
                "-T" + initial_changeset + " {node}\n"
            ],
            cwd=repo, stdout=subprocess.PIPE).stdout.decode('utf-8')
        with open(shamap, 'w') as fh:
            fh.write(content)

        subprocess.run(
            ['hg', 'convert', '--filemap', filemap, args.project_path, repo],
            stdout=subprocess.PIPE
        ).stdout.decode('utf-8')

        if args.push:
            out += subprocess.run(
                ['hg', 'push', '-r', 'default'],
                cwd=repo,
                stdout=subprocess.PIPE
            ).stdout.decode('utf-8')
            # Pull again
            out += hg_pull(repo)
    finally:
        os.remove(filemap)
    out += 'Finished migration for {}\n'.format(hg_locale)
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--push', action='store_true',
                        help='push results upstream')
    parser.add_argument('-p', default=4, metavar='N', help='Run N parallel jobs')
    parser.add_argument('project_path', metavar='Path to converted GitHub project')
    parser.add_argument(
        'l10n_path', metavar='Path to folder with clones of all l10n-central repositories')
    args = parser.parse_args()

    # Get a list of locales in the project
    project_locales = [
        dir
        for dir in os.listdir(os.path.join(args.project_path, gh_path_locales))
        if dir != 'en-US' and not dir.startswith('.')
    ]

    # Add ja-JP-mac
    project_locales.append('ja-JP-mac')
    project_locales.sort()

    # Limit to one locale for testing
    project_locales = ['it']

    handle = []
    skip = []
    for project_locale in project_locales:
        if os.path.isdir(os.path.join(args.l10n_path, project_locale)):
            handle.append(project_locale)
        else:
            skip.append(project_locale)

    migrate_fn = partial(migrate, args=args)
    with futures.ThreadPoolExecutor(max_workers=int(args.p)) as executor:
        for stdout in executor.map(migrate_fn, handle):
            sys.stdout.write(stdout)

    if skip:
        print('Skipped these locales: {}'.format(', '.join(skip)))


if __name__ == "__main__":
    main()
