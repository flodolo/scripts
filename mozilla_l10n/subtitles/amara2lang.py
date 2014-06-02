#!/usr/bin/env python

'''
Download English subtitles from video with id VIDEO_ID, convert them to .lang format

Usage: amara2lang.py video_id

Output: video_id.lang

IMPORTANT: set amara_apikey and amara_username to your values in order for
the script to work. This information can be saved in a file called auth.json,
using JSON format

{
	"amara_apikey": "API_ID",
	"amara_username": "USERNAME"
}

See also http://amara.readthedocs.org/en/latest/api.html

'''

import json
import StringIO
import sys
import urllib2

amara_apikey = ""
amara_username = ""

def readsrt(srtcontent):
	try:
		json_subtitles = {}
		srtfile = StringIO.StringIO(srtcontent)
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
	global amara_username
	global amara_apikey

	if amara_username == "" or amara_apikey == "":
		# Search for auth.json, try to set variables from it
		try:
			jsonfile = open("auth.json")
			api_data = json.load(jsonfile)
			amara_username = api_data["amara_username"]
			amara_apikey = api_data["amara_apikey"]
		except Exception as e:
			print e

	if amara_username == "" or amara_apikey == "":
		print "Error: missing mandatory parameters (Amara API key and username)"
		sys.exit(0)

	if len(sys.argv) != 2:
		print "Error: missing Amara video ID.\nSyntax: amara2lang.py videoID"
		sys.exit(0)

	video_id = sys.argv[1]
	lang_filename = video_id + ".lang"

	# Get subtitles in English
	print "Retrieving data from Amara..."
	url = "https://www.amara.org/api2/partners/videos/" + video_id + "/languages/en/subtitles/?format=srt"
	headers = {
		"X-api-username": amara_username,
		"X-apikey": amara_apikey
	}
	req = urllib2.Request(url, None, headers)
	try:
		response = urllib2.urlopen(req)
	except Exception as e:
		print e
		sys.exit(0)

	srtcontent = response.read()
	json_subtitles = readsrt(srtcontent)
	print "\nSaving data in " + lang_filename
	writelang(json_subtitles, lang_filename)


if __name__ == "__main__":
    main()
