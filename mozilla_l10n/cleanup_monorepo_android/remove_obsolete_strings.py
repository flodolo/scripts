#!/usr/bin/env python

from compare_locales import paths
from compare_locales.parser import getParser
from compare_locales.serializer import serialize
import argparse
import os
import sys


class StringExtraction:
    def __init__(self, toml_path, storage_path, reference_locale, repository_name):
        """Initialize object."""

        # Set defaults
        self.translations = {}
        self.storage_append = False
        self.storage_prefix = ""

        # Set instance variables
        self.toml_path = toml_path
        self.reference_locale = reference_locale
        self.repository_name = repository_name

    def extractStrings(self):
        """Extract strings from all locales."""

        def readFiles(locale):
            """Read files for locale"""

            if locale == self.reference_locale:
                files = paths.ProjectFiles(None, [project_config])
            else:
                files = paths.ProjectFiles(locale, [project_config])

            for l10n_file, reference_file, _, _ in files:
                if not os.path.exists(l10n_file):
                    # File not available in localization
                    continue

                if not os.path.exists(reference_file):
                    # File not available in reference
                    continue

                key_path = os.path.relpath(reference_file, basedir)
                # Prepend storage_prefix if defined
                if self.storage_prefix != "":
                    key_path = f"{self.storage_prefix}/{key_path}"
                try:
                    p = getParser(reference_file)
                except UserWarning:
                    continue

                p.readFile(l10n_file)
                self.translations[locale].update(
                    (
                        f"{self.repository_name}/{key_path}:{entity.key}",
                        entity.raw_val,
                    )
                    for entity in p.parse()
                )


def main():
    # Read command line input parameters
    p = argparse.ArgumentParser()
    p.add_argument("--toml", help="Path to root l10n.toml file", required=True)
    p.add_argument(
        "--locale", help="Run on a specific locale", action="store", default=""
    )
    args = p.parse_args()

    toml_path = args.toml
    basedir = os.path.dirname(toml_path)
    project_config = paths.TOMLParser().parse(toml_path, env={"l10n_base": ""})
    basedir = os.path.join(basedir, project_config.root)

    locales = [args.locale] if args.locale else project_config.all_locales
    for locale in locales:
        files = paths.ProjectFiles(locale, [project_config])
        for l10n_file, reference_file, _, _ in files:
            if not os.path.exists(l10n_file):
                # File not available in localization
                continue

            with open(reference_file) as f:
                source_content = f.read()
                source_parser = getParser(reference_file)
                source_parser.readUnicode(source_content)
                reference = list(source_parser.walk())
            with open(l10n_file) as f:
                target_content = f.read()
                target_parser = getParser(l10n_file)
                target_parser.readUnicode(target_content)
                target = list(target_parser.walk())

            output = serialize(l10n_file, reference, target, {})

            with open(l10n_file, "wb") as f:
                f.write(output)


if __name__ == "__main__":
    main()
