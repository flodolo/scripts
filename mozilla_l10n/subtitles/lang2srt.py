#!/usr/bin/env python

'''
Convert local lang file, created by srt2lang, into .srt format

Usage: lang2srt.py file_to_convert

Expect this format in the .lang file

# SUBTITLE_ID=>TIMING
;English subtitle (single line)
Translated subtitles (single line)
'''

import json
import os
import sys


def readlang(filename):
	try:
		json_subtitles = {}
		langfile = open(filename)
		current_index = timing = subtitle = ""
		for line in langfile:
			line = line.strip()
			if line != "":
				if line.startswith('#') and current_index == "":
					# Remove comment symbol and extra space, get index and timing
					line = line.lstrip('#').strip()
					current_index, timing = line.split("=>")
					current_index = int(current_index)
				else:
					# Ignore original starting with ;
					if not line.startswith(";"):
						# Read subtitle, replace <br> with \n
						subtitle = line.replace("<br>", "\n")
						# Store in json
						json_subtitles[current_index] = {
							"timing": timing.strip(),
							"subtitle": subtitle.strip()
						}
						current_index = ""

		# Debug
		# jsonfile = open("output.txt", "w")
		# jsonfile.write(json.dumps(json_subtitles, indent=4, sort_keys=True))
		# jsonfile.close()

		langfile.close()
		return json_subtitles
	except Exception as e:
		print e


def writesrt(subtitles, filename):
	try:
		srtfile = open(filename, "w")
		for index, subtitle in subtitles.iteritems():
			srtfile.write(str(index) + "\n")
			srtfile.write(subtitle["timing"] + "\n")
			srtfile.write(subtitle["subtitle"] + "\n\n")
		srtfile.close()
	except Exception as e:
		print e


def main():
	if len(sys.argv) != 2:
		print "Error: missing filename.\nSyntax: lang2srt.py examplefile.lang"
		sys.exit(0)

	lang_filename = sys.argv[1]

	if (os.path.splitext(lang_filename)[1] == ".lang"):
		srt_filename = os.path.splitext(lang_filename)[0] + ".srt"
	else:
		srt_filename = lang_filename + ".srt"

	print "\nExtracting data from " + lang_filename
	json_subtitles = readlang(lang_filename)
	print "\nSaving data in " + srt_filename
	writesrt(json_subtitles, srt_filename)


if __name__ == "__main__":
    main()
