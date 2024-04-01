#! /usr/bin/env python3

from compare_locales import parser
from urllib.request import urlopen
import argparse
import diff_match_patch as dmp_module
import json
import os
import subprocess
import sys


def extractFileList(repository_path):
    """
    Extract the list of supported files. Store the relative path and ignore
    specific folders for products we don't want to modify (e.g. SeaMonkey).
    """

    supported_formats = [
        ".dtd",
        ".ftl",
        ".ini",
        ".properties",
    ]

    excluded_folders = (
        ".hg",
        "calendar",
        "chat",
        "editor",
        "extensions",
        "mail",
        "other-licenses",
        "suite",
    )

    file_list = []
    for root, dirs, files in os.walk(repository_path, followlinks=True):
        # Ignore excluded folders
        if root == repository_path:
            dirs[:] = [d for d in dirs if d not in excluded_folders]

        for filename in files:
            if os.path.splitext(filename)[1] in supported_formats:
                filename = os.path.relpath(
                    os.path.join(root, filename), repository_path
                )
                file_list.append(filename)
    file_list.sort()

    return file_list


def extractStrings(file_list, repository_path):
    """Extract strings from all files."""

    translations = {}
    for file_name in file_list:
        file_path = os.path.join(repository_path, file_name)
        file_extension = os.path.splitext(file_path)[1]

        file_parser = parser.getParser(file_extension)
        file_parser.readFile(file_path)
        try:
            entities = file_parser.parse()
            for entity in entities:
                # Ignore Junk
                if isinstance(entity, parser.Junk):
                    continue
                string_id = "{}:{}".format(file_name, str(entity))
                if file_extension == ".ftl":
                    if entity.raw_val is not None:
                        translations[string_id] = entity.raw_val
                    # Store attributes
                    for attribute in entity.attributes:
                        attr_string_id = "{}:{}.{}".format(
                            file_name, str(entity), str(attribute)
                        )
                        translations[attr_string_id] = attribute.raw_val
                else:
                    translations[string_id] = entity.raw_val
        except Exception as e:
            print("Error parsing file: {}".format(file_name))
            print(e)

    return translations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("locale", help="Locale language code")
    parser.add_argument(
        "--start",
        help="Changeset used as starting point for the diff (default is the changeset shipping in release",
    )
    parser.add_argument(
        "--end",
        help="Changeset used as ending point for the diff (default is tip of the repository",
    )
    args = parser.parse_args()

    locale = args.locale
    repository_path = f"/Users/flodolo/mozilla/mercurial/l10n_clones/locales/{locale}/"

    if args.start:
        starting_changeset = args.start
    else:
        # Get the latest changeset shipping in release
        url = "https://hg.mozilla.org/releases/mozilla-release/raw-file/default/browser/locales/l10n-changesets.json"
        try:
            print("Reading l10n-changesets.json...")
            response = urlopen(url)
            json_data = json.load(response)
            if locale not in json_data:
                sys.exit(f"Locale {locale} not available in l10n-changesets.json")
            else:
                starting_changeset = json_data[locale]["revision"]
        except Exception as e:
            print(e)

    # Pull latest changes in the repository
    print("Updating repository...")
    subprocess.run(["hg", "-R", repository_path, "pull", "-u"])

    if args.end:
        ending_changeset = args.end
    else:
        # Get the long hash of the current tip
        ending_changeset = subprocess.check_output(
            ["hg", "-R", repository_path, "--debug", "id", "-i"]
        )
        ending_changeset = ending_changeset.strip().decode("utf-8")

        # Update to old revision
    print(f"Updating repository to revision {starting_changeset}...")
    subprocess.run(["hg", "-R", repository_path, "update", "-r", starting_changeset])
    # Generate file list and read the content
    print("Extracting strings...")
    old_file_list = extractFileList(repository_path)
    old_strings = extractStrings(old_file_list, repository_path)

    # Restore repository
    print(f"Updating repository to revision {ending_changeset}...")
    subprocess.run(["hg", "-R", repository_path, "update"])
    # Generate file list and read the content
    print("Extracting strings...")
    new_file_list = extractFileList(repository_path)
    new_strings = extractStrings(new_file_list, repository_path)

    # Restore to default
    print("Restoring repository to default...")
    subprocess.run(["hg", "-R", repository_path, "pull", "-u"])

    output = []
    dmp = dmp_module.diff_match_patch()
    for message_id, message in new_strings.items():
        if message_id not in old_strings:
            old_message = ""
        else:
            old_message = old_strings[message_id]
        if old_message == message:
            continue
        diff = dmp.diff_main(old_message, message)
        dmp.diff_cleanupSemantic(diff)
        output_element = """
        <tr>
            <td>{}</td>
            <td>{}</td>
        </tr>""".format(
            message_id, dmp.diff_prettyHtml(diff)
        )
        output.append(output_element)

    print("Saving diff to output.html")
    output_file = []
    with open("template.html", "r") as f:
        for line in f:
            if "%%BODY%%" in line:
                output_file.append("\n".join(output))
                continue
            if "%%LOCALE%%" in line:
                line = line.replace("%%LOCALE%%", locale)
            if "%%START_CHANGESET%%" in line:
                line = line.replace("%%START_CHANGESET%%", starting_changeset)
            if "%%END_CHANGESET%%" in line:
                line = line.replace("%%END_CHANGESET%%", ending_changeset)
            output_file.append(line)

    with open("output.html", "w") as f:
        f.writelines(output_file)

    subprocess.run(["open", "output.html"])


if __name__ == "__main__":
    main()
