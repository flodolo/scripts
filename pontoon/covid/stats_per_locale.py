"""
Get the monthly number of translation submissions per locale

Output is formatted as CSV with:
* A column for each locale
* First column in each row is the period

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

import datetime
from pontoon.base.models import *
from django.db.models.functions import TruncMonth


locales = Locale.objects.available().order_by("code")
data = {}

for year in range(2017, datetime.datetime.now().year + 1):
    for month in range(1, 13):
        if (
            year == datetime.datetime.now().year
            and month > datetime.datetime.now().month
        ):
            continue
        data["{}-{:02d}".format(year, month)] = {}

for locale in locales:
    translations = (
        Translation.objects.filter(
            date__gte=datetime.datetime(2017, 1, 1),
            locale=locale,
            user__isnull=False,
        )
        .annotate(period=TruncMonth("date"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )
    for x in translations:
        date = x["period"]
        date = "{}-{:02d}".format(date.year, date.month)
        count = x["count"]
        data[date][locale.code] = count

output = []
output.append("," + ",".join(locales.values_list("code", flat=True)))
for date, values in data.items():
    line = date
    for locale in locales:
        line = line + "," + str(values.get(locale.code, 0))
    output.append(line)

print("\n".join(output))
