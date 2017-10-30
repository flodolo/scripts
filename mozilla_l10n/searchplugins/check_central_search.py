#! /usr/bin/env python

import argparse
import glob
import json
import os

class SearchChecker():

    def __init__(self, sp_path, product):
        ''' Initialize object '''
        self.base_path = os.path.join(sp_path, product, 'locales')
        self.product = product

        self.sp_list = self.extract_list()
        self.unused = self.sp_list[:]
        self.errors = []


    def analyze(self):
        '''Analyze searchplugins'''
        with open(os.path.join(self.base_path, 'search', 'list.json')) as f:
            sp_settings = json.load(f)

        # Check default
        for sp in sp_settings['default']['visibleDefaultEngines']:
            self.check_sp(sp)

        # Check regions
        for region in sp_settings['regionOverrides']:
            for sp, sp_override in sp_settings['regionOverrides'][region].iteritems():
                self.check_sp(sp_override)

        # Check locales
        for locale in sp_settings['locales']:
            locale_data = sp_settings['locales'][locale]
            for sp in locale_data['default']['visibleDefaultEngines']:
                self.check_sp(sp)
            if 'experimental-hidden' in locale_data:
                for sp in locale_data['experimental-hidden']['visibleDefaultEngines']:
                    self.check_sp(sp)

        if len(self.unused):
            self.unused.sort()
            self.errors.append('\nERROR: there are unused searchplugins ({}) in {}'.format(len(self.unused), self.product))
            self.errors.append('\n'.join(self.unused))

        if len(self.errors):
            print('\n'.join(self.errors))
        else:
            print('There are no errors for {}.'.format(self.product))

    def extract_list(self):
        '''Store a list of XML files in sp_path'''
        sp_list = []
        try:
            for searchplugin in glob.glob(os.path.join(self.base_path, 'searchplugins', '*.xml')):
                searchplugin_noext = os.path.splitext(os.path.basename(searchplugin))[0]
                sp_list.append(searchplugin_noext)
        except Exception as e:
            print('Error: problem reading list of shared searchplugins from {0}'.format(sp_path))
            print(e)

        return sp_list

    def check_sp(self, sp):
        if sp not in self.sp_list:
            self.errors.append('ERROR: {} is not available in the list of XML files'.format(sp))
        else:
            if sp in self.unused:
                # Mark the searchplugin as used by removing it from the list of unused files
                self.unused.remove(sp)


def main():
    # Parse command line options
    cl_parser = argparse.ArgumentParser()
    cl_parser.add_argument('repo_path', help='Path to mozilla-unified or mozilla-central clone')
    args = cl_parser.parse_args()

    for product in ['browser', 'mobile']:
        spcheck = SearchChecker(args.repo_path, product)
        spcheck.analyze()


if __name__ == "__main__":
    main()
