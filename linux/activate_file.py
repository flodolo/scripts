#! /usr/bin/env python

import argparse
import json
import os
import re
import urllib2

langchecker_url = 'http://l10n.mozilla-community.org/~pascalc/langchecker/'
langchecker_url = 'http://192.168.133.115/langchecker/'

def activate_file(filename):
    with open(filename,'r+') as f:
        content = f.read()
        f.seek(0,0)
        f.write("## active ##\n" + content)

def main(filename):
	complete_locales_json = langchecker_url + "?locale=all&website=0&json&file=" + filename

	# Analyze complete pages
	try:
		# Read langchecker
		response = urllib2.urlopen(complete_locales_json)
		json_data = json.load(response)

		# Get a list of complete locales still not activated
		locales_to_activate = []
		for locale in json_data[filename]:
			activated = json_data[filename][locale]["activated"]
			missing_strings = json_data[filename][locale]["Missing"] + json_data[filename][locale]["Identical"]
			completed = False if missing_strings > 0 else True

			if completed and not activated:
				locales_to_activate.append(locale)
	except Exception as e:
		print "Error reading json file from " + activated_locales_url
		print e

	# Add active tags
	if locales_to_activate:
		locales_to_activate.sort()
		print "Activated locales: "
		for locale in locales_to_activate:
			try:
				activate_file(locale + "/" + filename)
				print locale
			except Exception as e:
				print "File missing for " + locale
	else:
		print "No locales ready for activation"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    main(args.filename)
