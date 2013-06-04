#! /usr/bin/env python

import json
import datetime

json_data=open('package.json')
data = json.load(json_data)

# Replace original ID
data["id"] = 'r2d2b2g-l10n@mozilla.org'

# Replace addon version (originalversion -> originalversion.YYYYMMDD)
oldAddonVersion = data["version"]
newAddonVersion = oldAddonVersion + '.' + datetime.date.today().strftime('%Y%m%d')
data["version"] = newAddonVersion

json_data.close()

# Write back updated json data
packageFile = open("package.json", "w")
packageFile.write(json.dumps(data, indent=4, sort_keys=True))
packageFile.close()
