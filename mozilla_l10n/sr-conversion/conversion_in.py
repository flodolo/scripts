#!/usr/bin/env python

# Original script: https://gist.github.com/Pike/6525641

import os
import subprocess

revs = []
hg_cyrl = ['hg', '-R', 'sr-Cyrl']
hg_latn = ['hg', '-R', 'sr-Latn']
uconv = '/usr/local/opt/icu4c/bin/uconv'

try:
    revs = subprocess.check_output(hg_cyrl + ['-q', 'in',
                                   '--template', '{rev}\n']).split()
except Exception as e:
    print "No incoming changesets"

if revs:
    for rev in revs:
        print rev
        subprocess.check_call(hg_cyrl + ['pull', '-u', 'default'])
        subprocess.check_call(hg_cyrl + ['update', '-r', rev])
        author = subprocess.check_output(hg_cyrl + ['log', '-r', '.', '--template','{author}'])
        files = subprocess.check_output(hg_cyrl + ['log', '-r', '.', '--template','{files}']).split()
        desc = subprocess.check_output(hg_cyrl + ['log', '-r', '.', '--template','{desc}'])
        for f in files:
            file_latn = 'sr-Latn/' + f
            file_cyrl = 'sr-Cyrl/' + f
            if not os.path.isfile(file_latn):
                # If the same file doesn't exist in sr-Latn, script fails
                path_latn = os.path.dirname(file_latn)
                if not os.path.exists(path_latn):
                    # Create folder too since is missing
                    os.makedirs(path_latn)
                    print "Creating missing folders: " + path_latn
                open(file_latn, 'a').close()
                print 'Adding file to repo: ' + file_latn
                subprocess.check_call(hg_latn + ['add', file_latn])
            if not os.path.isfile(file_cyrl):
                # File has been deleted from sr-Cyrl, can't convert this one
                # File has been deleted from sr-Cyrl, can't convert this one
                print 'Removing file from repo: ' + file_latn
                subprocess.check_call(hg_latn + ['remove', file_latn])
                continue
            subprocess.check_call([uconv, '-x', 'Serbian-Latin/BGN',
                                   '-o', file_latn, file_cyrl])

        # Commit changeset
        subprocess.check_call(hg_latn + ['ci', '-m', desc, '-u', author])
