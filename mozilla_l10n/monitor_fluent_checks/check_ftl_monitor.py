#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys

from configparser import SafeConfigParser
from compare_locales import parser

class StringExtraction():

    def __init__(self, repository_path, reference_locale):
        '''Initialize object.'''

        # Set defaults
        self.supported_formats = [
            '.ftl',
        ]
        self.translations = {}
        self.fluent_placeables = {}
        self.fluent_tags = {}

        self.locales_path = os.path.join(repository_path, 'locales')
        self.reference_locale = reference_locale

        # Get the list of locales available
        self.locales = self.getLocalesList()

    def getLocalesList(self):
        '''Get list of supported locales'''

        locales = [f.name for f in os.scandir(self.locales_path) if f.is_dir()]
        locales.sort()

        return locales

    def extractFileList(self, locale):
        '''Extract the list of supported files.'''

        locale_path = os.path.join(self.locales_path, locale)
        file_list = []
        for root, dirs, files in os.walk(locale_path, followlinks=True):
            for file in files:
                for supported_format in self.supported_formats:
                    if file.endswith(supported_format):
                        file_list.append(os.path.join(root, file))
        file_list.sort()

        return file_list

    def getRelativePath(self, file_name, locale):
        '''
        Get the relative path of a filename, prepend prefix_storage if
        defined.
        '''

        locale_path = os.path.join(self.locales_path, locale)
        relative_path = file_name[len(locale_path) + 1:]

        return relative_path

    def extractStrings(self):
        '''Extract strings from all files.'''

        # Read strings for all locales, including the reference locale
        print('Parsing locales')
        for locale in self.locales:
            # Create a list of files to analyze
            file_list = self.extractFileList(locale)
            self.translations[locale] = {}

            for file_name in file_list:
                file_extension = os.path.splitext(file_name)[1]

                file_parser = parser.getParser(file_extension)
                file_parser.readFile(file_name)
                try:
                    entities = file_parser.parse()
                    for entity in entities:
                        # Ignore Junk
                        if isinstance(entity, parser.Junk):
                            continue
                        string_id = '{}:{}'.format(
                            self.getRelativePath(file_name, locale), entity)
                        if file_extension == '.ftl':
                            if entity.raw_val is not None:
                                self.translations[locale][string_id] = entity.raw_val
                            # Store attributes
                            for attribute in entity.attributes:
                                attr_string_id = '{}:{}.{}'.format(
                                    self.getRelativePath(file_name, locale),
                                    entity,
                                    attribute)
                                self.translations[locale][attr_string_id] = \
                                    attribute.raw_val
                        else:
                            self.translations[locale][string_id] = entity.raw_val
                except Exception as e:
                    print('Error parsing file: {}'.format(file_name))
                    print(e)

        # Remove extra strings from locale
        reference_ids = list(self.translations[self.reference_locale].keys())
        for locale in self.locales:
            if locale == self.reference_locale:
                continue

            for string_id in list(self.translations[locale].keys()):
                if string_id not in reference_ids:
                    del(self.translations[locale][string_id])

    def analysePlaceables(self, string_id, message):
        '''Analyze text for Fluent placeable (variables, terms, etc.)'''

        placeables_pattern = re.compile(
            '(?<!\{)\{\s*([\$|-]?[A-Za-z0-9_-]+)(?:[\[(]?[A-Za-z0-9_\-, :"]+[\])])*\s*\}', re.UNICODE)
        placeables_iterator = placeables_pattern.finditer(message)
        placeables = []
        for m in placeables_iterator:
            placeables.append(m.group(1))

        # Only look for unique placeables. Some error might be ignored, but
        # otherwise all plural forms will have errors
        placeables = list(set(placeables))
        placeables.sort()

        return placeables

    def analyseTags(self, string_id, message):
        '''Analyze HTML tags'''

        tags_pattern = re.compile(
            "(</?\w+(?:(?:\s+\w+(?:\s*=\s*(?:\".*?\"|'.*?'|[\^'\">\s]+))?)+\s*|\s*)/?>)", re.UNICODE)
        tags_iterator = tags_pattern.finditer(message)
        tags = []
        for m in tags_iterator:
            tags.append(m.group(1))

        # Only look for unique tags. Some error might be ignored, but
        # otherwise all plural forms will have errors
        tags = list(set(tags))
        tags.sort()

        return tags


    def checkFTL(self):
        '''Run Fluent checks'''

        print('Running Fluent checks')
        errors = {}

        # Analyze reference locale for placeables
        for string_id, message in self.translations[self.reference_locale].items():
            placeables = self.analysePlaceables(string_id, message)
            if placeables:
                self.fluent_placeables[string_id] = placeables
            tags = self.analyseTags(string_id, message)
            if tags:
                self.fluent_tags[string_id] = tags

        # Analyze locales
        for locale in self.locales:
            if locale == self.reference_locale:
                continue

            errors[locale] = []

            for string_id, translation in self.translations[locale].items():
                # Check for stray spaces
                if '{ "' in translation:
                    error_msg = 'Fluent literal in string ({})'.format(
                        string_id)
                    errors[locale].append(' {}'.format(error_msg))
                    errors[locale].append('  {}'.format(translation))

                # Check for DTD variables, e.g. '&something;'
                pattern = re.compile('&.*;', re.UNICODE)
                if pattern.search(translation):
                    error_msg = 'XML entity in Fluent string ({})'.format(
                        string_id)
                    errors[locale].append(' {}'.format(error_msg))
                    errors[locale].append('  {}'.format(translation))

                # Check for properties variables '%S' or '%1$S'
                pattern = re.compile(
                    '(%(?:[0-9]+\$){0,1}(?:[0-9].){0,1}([sS]))', re.UNICODE)
                if pattern.search(translation):
                    error_msg = 'printf variables in Fluent string ({})'.format(
                        string_id)
                    errors[locale].append(' {}'.format(error_msg))
                    errors[locale].append('  {}'.format(translation))

                # Check for the message ID repeated in the translation
                message_id = string_id.split(':')[1]
                pattern = re.compile(
                    re.escape(message_id) + '\s*=', re.UNICODE)
                if pattern.search(translation):
                    error_msg = 'Message ID is repeated in the Fluent string ({})'.format(
                        string_id)
                    errors[locale].append(' {}'.format(error_msg))
                    errors[locale].append('  {}'.format(translation))

                # Check placeables
                placeables = self.analysePlaceables(string_id, translation)
                if placeables:
                    if not string_id in self.fluent_placeables:
                        error_msg = 'Strings has more placeables than reference ({})'.format(
                            string_id)
                        errors[locale].append(' {}'.format(error_msg))
                        errors[locale].append('  {}: {}'.format(self.reference_locale, self.translations[self.reference_locale][string_id]))
                        errors[locale].append('  {}: {}'.format(locale, translation))
                    else:
                        if placeables != self.fluent_placeables[string_id]:
                            error_msg = 'Placeables mismatch with reference ({})'.format(
                                string_id)
                            errors[locale].append(' {}'.format(error_msg))
                            errors[locale].append('  {}: {}'.format(self.reference_locale,
                                                    self.translations[self.reference_locale][string_id]))
                            errors[locale].append('  {}: {}'.format(locale, translation))
                else:
                    if string_id in self.fluent_placeables:
                        error_msg = 'Missing placeables compared to reference ({})'.format(
                            string_id)
                        errors[locale].append(' {}'.format(error_msg))
                        errors[locale].append('  {}: {}'.format(self.reference_locale,
                                               self.translations[self.reference_locale][string_id]))
                        errors[locale].append(
                            '  {}: {}'.format(locale, translation))

                # Check tags
                tags = self.analyseTags(string_id, translation)
                if tags:
                    if not string_id in self.fluent_tags:
                        error_msg = 'Strings has more tags than reference ({})'.format(
                            string_id)
                        errors[locale].append(' {}'.format(error_msg))
                        errors[locale].append('  {}: {}'.format(self.reference_locale, self.translations[self.reference_locale][string_id]))
                        errors[locale].append(
                            '  {}: {}'.format(locale, translation))
                    else:
                        if tags != self.fluent_tags[string_id]:
                            error_msg = 'Tags mismatch with reference ({})'.format(
                                string_id)
                            errors[locale].append(' {}'.format(error_msg))
                            errors[locale].append('  {}: {}'.format(self.reference_locale,
                                                    self.translations[self.reference_locale][string_id]))
                            errors[locale].append(
                                '  {}: {}'.format(locale, translation))
                else:
                    if string_id in self.fluent_tags:
                        error_msg = 'Missing tags compared to reference ({})'.format(
                            string_id)
                        errors[locale].append(' {}'.format(error_msg))
                        errors[locale].append('  {}: {}'.format(self.reference_locale,
                                               self.translations[self.reference_locale][string_id]))
                        errors[locale].append(
                            '  {}: {}'.format(locale, translation))

        errored = False
        for locale, locale_errors in errors.items():
            if locale_errors:
                errored = True
                print('Locale: {}'.format(locale))
                print('\n'.join(locale_errors))

        if not errored:
            print('No errors found.')


def main():
    # Reference locale
    reference_locale = 'en'

    # Read command line input parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('repo_path', help='Path to blurts-server clone')
    args = parser.parse_args()

    extracted_strings = StringExtraction(args.repo_path, reference_locale)
    extracted_strings.extractStrings()
    extracted_strings.checkFTL()


if __name__ == '__main__':
    main()
