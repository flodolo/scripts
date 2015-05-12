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
        cycle_length = 30
        end_date = datetime.strptime(data['nextReset'], "%Y-%m-%d %H:%M:%S")
        remaining_days = abs((end_date - datetime.today()).days);
        if cycle_length - remaining_days > 0:
            used_days = cycle_length - remaining_days
        else:
            used_days = 1
        # Data quota/usage
        quota_mb = data['quota'] / 1024
        used_mb = data['used'] / 1024
        remaining_mb = quota_mb - used_mb
        # Print values
        print "Rimamenti:        %5.0f MB" % remaining_mb
        print "Quota:            %5.0f MB" % quota_mb
        print "Giorni:              %2.0f g" % remaining_days
        # Avoid division by 0
        if remaining_days == 0:
            remaining_days = 1;
        print "Media consumo:    %5.0f MB/g" % \
              (used_mb / used_days)
        print "Media dispon.:    %5.0f MB/g" % \
              (remaining_mb / remaining_days)
except urllib2.HTTPError, err:
    if err.code == 403:
        print "Errore 403 - Connessione non Eolo"
    else:
        raise
except Exception as e:
    print "Errore lettura JSON da %s:\n %s" % (eolo_url, e)
