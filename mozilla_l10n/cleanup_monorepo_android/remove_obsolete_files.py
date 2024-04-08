#!/usr/bin/env python3

"""

This script is used in an Android repository to remove obsolete localized files.

"""

import argparse
import os
import re


def extractFileList(repository_path):
    file_list = []
    for root, dirs, files in os.walk(repository_path, followlinks=True):
        for filename in files:
            if os.path.splitext(filename)[1] == ".xml":
                filename = os.path.relpath(
                    os.path.join(root, filename), repository_path
                )
                file_list.append(filename)
    file_list.sort()

    return file_list


def main():
    p = argparse.ArgumentParser(description="Remove obsolete files")
    p.add_argument("--path", help="Path to repository", required=True)
    args = p.parse_args()

    repo_path = args.path
    file_list = extractFileList(repo_path)

    obsolete_files = []
    for f in file_list:
        ref_file = re.sub(r"values\-.*\/", "values/", f)
        if ref_file not in file_list:
            obsolete_files.append(f)
    obsolete_files.sort()

    for f in obsolete_files:
        os.remove(f)


if __name__ == "__main__":
    main()
