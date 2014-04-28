#! /usr/bin/env python

import json
import os
import re
import urllib2

def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]

def print_array(locales):
	if locales:
		print ', '.join(locales)
	else:
		print "(no locales)"

os.system('clear')

pages = [
	{
		"filename": "firefox/channel.lang",
		"rule_check": "/b/$1/firefox/channel$2 [PT]"
	},
	{
		"filename": "firefox/new.lang",
		"rule_check": "/b/$1/firefox/new$2 [PT]"
	},
	{
		"filename": "mozorg/plugincheck.lang",
		"rule_check": "/b/$1/plugincheck$2 [PT]"
	}
]

for page in pages:
	# URL to extract activated pages from langchecker's json
	filename = page['filename']
	activated_locales_url = "http://l10n.mozilla-community.org/~pascalc/langchecker/?locale=all&website=0&json&file=" + filename

	# URL to extract locales currently included in rewrite rule
	rewrite_rule_url = "https://raw.githubusercontent.com/mozilla/bedrock/master/etc/httpd/global.conf"
	rule_ending = page['rule_check']

	# Analyze active pages
	try:
		activated_locales = []
		warning_locales = []
		response = urllib2.urlopen(activated_locales_url)
		json_data = json.load(response)
		for locale in json_data[filename]:
			activated = json_data[filename][locale]["activated"]
			missing_strings = json_data[filename][locale]["Missing"] + json_data[filename][locale]["Identical"]
			if (activated):
				activated_locales.append(locale)
				if (missing_strings > 0):
					warning_locales.append(locale)
		activated_locales.sort()
		warning_locales.sort()
	except Exception as e:
		print "Error reading json file from " + activated_locales_url
		print e

	# Analyze rewrite rule
	rewrite_rule_locales = ""
	for line in urllib2.urlopen(rewrite_rule_url):
		if rule_ending in line:
			rewrite_rule_locales = line
	search_result = re.search('\((.*?)\)', rewrite_rule_locales).group(1)
	rewrite_rule_locales = search_result.split("|")

	# Print results
	print "**************************************************************"
	print "             Checking: " + filename
	print "**************************************************************"
	print "\nRewrite rule current content"
	print_array(rewrite_rule_locales)
	print "\nActivated locales"
	print_array(activated_locales)
	print "\nLocales activated with missing or identical strings"
	print_array(warning_locales)
	print "\nAll locales missing from rewrite rule"
	missing_locales = diff(activated_locales, rewrite_rule_locales)
	print_array(missing_locales)
	print "\nComplete locales missing from rewrite rule"
	missing_complete_locales = diff(diff(activated_locales,warning_locales), rewrite_rule_locales)
	print_array(missing_complete_locales)
