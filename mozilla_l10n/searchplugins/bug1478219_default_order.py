#! /usr/bin/env python3

import fileinput
import glob
import os
import hglib
from hglib.util import b


def main():
    locales_folder = '/Users/flodolo/mozilla/mercurial/l10n_clones/locales'
    locales = sorted(os.listdir(locales_folder))

    target_files = [
        os.path.join('browser', 'chrome', 'browser-region', 'region.properties'),
        os.path.join('mobile', 'chrome', 'region.properties')
    ]

    lines_to_remove = (
        '# Default search',
        'browser.search.defaultenginename',
        '# Search engine order',
        'browser.search.order.',
    )

    #locales = ['ach']

    for locale in locales:
        if not locale.startswith('.'):
            locale_repo = os.path.join(locales_folder, locale)

            # Pull repository
            client = hglib.open(locale_repo)
            client.pull(update=True, branch='default')

            for target_file in target_files:
                region_file = os.path.join(locale_repo, target_file)

                if os.path.isfile(region_file):
                    searchfile = fileinput.input(region_file, inplace=1)
                    for line in searchfile:
                        if line.startswith(lines_to_remove):
                            continue
                        print(line, end='')
                    searchfile.close()

                    searchfile = fileinput.input(region_file, inplace=1)
                    empty_line = False
                    for line in searchfile:
                        if line.rstrip() == '':
                            if empty_line:
                                # Remove multiple consecutive empty lines
                                continue
                            empty_line = True
                        else:
                            empty_line = False
                        print(line, end='')
                    searchfile.close()

            # Commit files removal and push
            try:
                client.commit(
                    b('Bug 1478219 - Remove search default and order from region.properties'), addremove=True)
                client.push(branch='default')
                print('Pushed changes to https://hg.mozilla.org/l10n-central/{}'.format(locale))
            except:
                print('Nothing to push for {}'.format(locale))


if __name__ == '__main__':
    main()
