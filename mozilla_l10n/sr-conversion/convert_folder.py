#! /usr/bin/env python

import os
import subprocess

def main():
    uconv = '/usr/local/opt/icu4c/bin/uconv'
    sourcefolder = 'sr-Cyrl'
    destfolder = 'sr-Latn'
    sourcepath = os.path.join(os.getcwd(), sourcefolder)
    destpath = os.path.join(os.getcwd(), destfolder)
    filelist = []

    for root, dirnames, filenames in os.walk(sourcepath):
        for filename in filenames:
            if '.hg' not in root and '.hg' not in filename:
                filelist.append(os.path.join(root, filename))

    for sourcefile in filelist:
        # Full path to destination file
        relativepath = sourcefile[len(sourcepath):]
        destfile = os.path.join(destpath, relativepath.lstrip(os.sep))

        # Check if folder exists, if note create it
        containerfolder = os.path.dirname(destfile)
        if not os.path.exists(containerfolder):
            print "Creating folder: " + containerfolder
            os.makedirs(containerfolder);

        # Convert the file
        subprocess.check_call([uconv, '-x', 'Serbian-Latin/BGN', '-o', destfile, sourcefile])

if __name__ == '__main__':
    main()