#! /usr/bin/env python

import json
import urllib2
from datetime import datetime

eolo_url = "https://care.ngi.it/ws/ws.asp?a=get.quota"
try:
    response = urllib2.urlopen(eolo_url)
    json_data = json.load(response)
    if json_data['response']['status'] == 200:
        data = json_data['data']
        # Days before reset
        end_date = datetime.strptime(data['nextReset'], "%Y-%m-%d %H:%M:%S")
        remaining_days = abs((end_date - datetime.today()).days)
        # Data quota/usage
        quota_mb = data['quota'] / 1024
        used_mb = data['used'] / 1024
        remaining_mb = quota_mb - used_mb
        # Print values
        print "Rimamenti:        %5.0f MB" % remaining_mb
        print "Quota:            %5.0f MB" % quota_mb
        print "Giorni:              %2.0f g" % remaining_days
        print "Media consumo:    %5.0f MB/g" % \
              (used_mb / (30 - remaining_days))
        print "Media dispon.:    %5.0f MB/g" % \
              (remaining_mb / remaining_days)

except Exception as e:
    print "Error reading json file from " + eolo_url
    print e
