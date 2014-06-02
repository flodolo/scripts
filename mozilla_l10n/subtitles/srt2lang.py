#!/usr/bin/env python

'''
Convert local subtitle file downloaded from Amara into .lang format

Usate: srt2lang.py file_to_convert

Expect this format in the .srt file

SUBTITLE_ID
TIMING
Subtitles (multiline)

Empty line marks the end of subtitle.
'''

# Convert .srt file from Amara into .lang file

import json
import os
import sys


def readsrt(filename):
	try:
		json_subtitles = {}
		srtfile = open(filename)
		current_index = timing = subtitle = ""
		for line in srtfile:
			line = line.strip()
			if line != "":
				if current_index == "":
					# Start of this subtitle
					try:
						current_index = int(line)
					except Exception as e:
						print e
				else:
					if timing == "":
						# Timing information
						timing = line
					else:
						if subtitle == "":
							# Start of actual subtitle
							subtitle = line
						else:
							# Multiline subtitle
							subtitle = subtitle + "<br>" + line
			else:
				# End of this subtitle
				json_subtitles[current_index] = {
					"timing": timing,
					"subtitle": subtitle
				}
				current_index = timing = subtitle = ""

		# Reached end of file, save the last subtitle
		json_subtitles[current_index] = {
			"timing": timing,
			"subtitle": subtitle
		}

		# Debug
		# jsonfile = open("output.txt", "w")
		# jsonfile.write(json.dumps(json_subtitles, indent=4, sort_keys=True))
		# jsonfile.close()

		srtfile.close()
		return json_subtitles
	except Exception as e:
		print e


def writelang(subtitles, filename):
	try:
		langfile = open(filename, "w")
		for index, subtitle in subtitles.iteritems():
			langfile.write("# " + str(index) + "=>" + subtitle["timing"] + "\n")
			langfile.write(";" + subtitle["subtitle"] + "\n")
			langfile.write(subtitle["subtitle"] + "\n\n\n")
		langfile.close()
	except Exception as e:
		print e


def main():
	if len(sys.argv) != 2:
		print "Error: missing filename.\nSyntax: srt2lang.py examplefile.srt"
		sys.exit(0)

	srt_filename = sys.argv[1]

	if (os.path.splitext(srt_filename)[1] == ".srt"):
		lang_filename = os.path.splitext(srt_filename)[0] + ".lang"
	else:
		lang_filename = srt_filename + ".lang"

	print "\nExtracting data from " + srt_filename
	json_subtitles = readsrt(srt_filename)
	print "\nSaving data in " + lang_filename
	writelang(json_subtitles, lang_filename)


if __name__ == "__main__":
    main()
