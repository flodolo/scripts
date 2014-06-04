#!/usr/bin/env python

'''
Upload file to Amara.

Usage: uploadtoamara.py video_id locale_id srt_file

IMPORTANT: set amara_apikey and amara_username to your values in order for
the script to work. This information can be saved in a file called auth.txt,
using JSON format

{
	"amara_apikey"   : "API_ID",
	"amara_username" : "USERNAME"
}

See also http://amara.readthedocs.org/en/latest/api.html

'''

import json
import sys
import urllib2


# Add your amara auth data
authdata = {
	"username" : "",
	"apikey"   : ""
}


def getRequest(url, authdata):
	headers = {
		"Accept"         : "application/json",
		"X-api-username" : authdata["username"],
		"X-apikey"       : authdata["apikey"]
	}
	req = urllib2.Request(url, None, headers)
	try:
		response = urllib2.urlopen(req)
		return {
			"success" : True,
			"result"  : response.read()
		}
	except Exception as e:
		return {
			"success" : False,
			"result"  : e.code
		}


def postRequest(url, values, authdata):
	headers = {
		"Content-Type"   : "application/json",
		"X-api-username" : authdata["username"],
		"X-apikey"       : authdata["apikey"]
	}
	req = urllib2.Request(url, json.dumps(values), headers)
	try:
		response = urllib2.urlopen(req)
		return {
			"success" : True,
			"result"  : response.read()
		}
	except Exception as e:
		return {
			"success" : False,
			"result"  : e
		}


def main():
	global authdata

	if authdata["username"] == "" or authdata["apikey"] == "":
		# Search for auth.json, try to set variables from it
		try:
			jsonfile = open("auth.json")
			api_data = json.load(jsonfile)
			authdata["username"] = api_data["amara_username"]
			authdata["apikey"]   = api_data["amara_apikey"]
		except Exception as e:
			print e

	if authdata["username"] == "" or authdata["apikey"] == "":
		print "Error: missing mandatory parameters (Amara API key and username)"
		sys.exit(0)

	if len(sys.argv) != 4:
		print "Error: wrong number of parameters.\nSyntax: uploadtoamara.py videoid localeid srtfile"
		sys.exit(0)

	video_id     = sys.argv[1]
	locale_id    = sys.argv[2]
	srt_filename = sys.argv[3]

	# Read subtitles
	try:
		srtfile = open(srt_filename).read()
	except Exception as e:
		print "There was an error reading the file."
		print e
		sys.exit(0)

	# Check if this language exists
	print "\nChecking if language exists..."
	url = "https://www.amara.org/api2/partners/videos/" + video_id + "/languages/" + locale_id + "/"
	response = getRequest(url, authdata)
	if not response["success"] and response["result"] == 404:
		missing_language = True
	else:
		missing_language = False

	# Missing language, need to create it
	if missing_language:
		print "Language is missing on Amara, creating..."
		url = "https://www.amara.org/api2/partners/videos/" + video_id + "/languages/"
		values = {
			"language_code": locale_id
		}
		response = postRequest(url, values, authdata)
		if not response["success"]:
			print "There was an error"
			print response["result"]
			sys.exit(0)

	# Uploading a file
	print "Uploading file to Amara..."
	url = "https://www.amara.org/api2/partners/videos/" + video_id + "/languages/" + locale_id + "/subtitles/"
	values = {
		"sub_format": "srt",
		"subtitles": srtfile
	}
	response = postRequest(url, values, authdata)
	if not response["success"]:
		print "There was an error"
		print response["result"]
	else:
		json_response = json.loads(response["result"])
		print "File uploaded. Subtitle version: ", json_response["version_number"]


if __name__ == "__main__":
    main()
