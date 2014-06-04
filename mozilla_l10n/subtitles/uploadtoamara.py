#!/usr/bin/env python

'''
Upload file to Amara.

Usage: uploadtoamara.py video_id locale_id srt_file

IMPORTANT: set amara_apikey and amara_username to your values in order for
the script to work. This information can be saved in a file called auth.txt,
using JSON format

{
	"amara_apikey": "API_ID",
	"amara_username": "USERNAME"
}

See also http://amara.readthedocs.org/en/latest/api.html

'''

import json
import sys
import urllib2

amara_apikey = ""
amara_username = ""

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

	if len(sys.argv) != 4:
		print "Error: missing parameters.\nSyntax: uploadtoamara.py videoid localeid srtfile"
		sys.exit(0)

	video_id = sys.argv[1]
	locale_id = sys.argv[2]
	srt_filename = sys.argv[3]

	# Read subtitles
	try:
		srtfile = open(srt_filename).read()
	except Exception as e:
		print e

	print "Uploading file to Amara..."
	url = "https://www.amara.org/api2/partners/videos/" + video_id + "/languages/" + locale_id + "/subtitles/"

	headers = {
		"Content-Type": "application/json",
		"X-api-username": amara_username,
		"X-apikey": amara_apikey
	}
	values = {
		"sub_format": "srt",
		"subtitles": srtfile
	}

	req = urllib2.Request(url, json.dumps(values), headers)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except Exception as e:
		print e
		sys.exit(0)



if __name__ == "__main__":
    main()
