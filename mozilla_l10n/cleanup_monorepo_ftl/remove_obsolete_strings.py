#!/usr/bin/env python3

"""

This script is used in a monorepo to remove obsolete strings and reformat files
accordingly to the reference locale.

By default, the script runs on all locales.

"""

from compare_locales.parser import getParser
from compare_locales.serializer import serialize
import argparse
import os
import sys


def extractFileList(repository_path):
    file_list = []
    for root, dirs, files in os.walk(repository_path, followlinks=True):
        for filename in files:
            if os.path.splitext(filename)[1] == ".ftl":
                filename = os.path.relpath(
                    os.path.join(root, filename), repository_path
                )
                file_list.append(filename)
    file_list.sort()

    return file_list


def main():
    p = argparse.ArgumentParser(
        description="Remove obsolete strings and reformat files"
    )
    p.add_argument("--path", help="Path to repository", required=True)
    p.add_argument("--ref", help="Reference locale code (folder)", required=True)
    p.add_argument("--delete", help="Delete extra files", action="store_true")
    p.add_argument(
        "--locale", help="Run on a specific locale", action="store", default=""
    )
    args = p.parse_args()

    repo_path = args.path
    if args.locale:
        locales = [args.locale]
    else:
        locales = [
            x
            for x in os.listdir(repo_path)
            if not x.startswith(".")
            and os.path.isdir(os.path.join(repo_path, x))
            and x != args.ref
        ]
        locales.sort()

    # Get a list of supported files in the reference folder
    ref_path = os.path.join(repo_path, args.ref)
    if not os.path.exists(ref_path):
        sys.exit(f"The reference folder doesn't exist ({ref_path})")
    source_file_list = extractFileList(ref_path)

    for locale in locales:
        print("Locale: {}".format(locale))
        locale_path = os.path.join(repo_path, locale)

        # Create list of target files
        target_file_list = extractFileList(locale_path)

        # If --delete is requested, remove extra files in locale folders.
        if args.delete:
            extra_files = [f for f in target_file_list if f not in source_file_list]
            for f in extra_files:
                os.remove(os.path.join(locale_path, f))

        target_file_list = [f for f in target_file_list if f in source_file_list]

        # Read source and target and write the output overwriting the existing
        # localized file
        for filename in target_file_list:
            source_filename = os.path.join(ref_path, filename)
            target_filename = os.path.join(locale_path, filename)
            with open(source_filename) as f:
                source_content = f.read()
                source_parser = getParser(filename)
                source_parser.readUnicode(source_content)
                reference = list(source_parser.walk())
            with open(target_filename) as f:
                target_content = f.read()
                target_parser = getParser(filename)
                target_parser.readUnicode(target_content)
                target = list(target_parser.walk())

            output = serialize(filename, reference, target, {})

            with open(target_filename, "wb") as f:
                f.write(output)


if __name__ == "__main__":
    main()
