"""
Get the monthly number of new registrations, active users and submitted translations.

Output is formatted as CSV with the following columns:
* Period (month, year)
* Number of new user registered
* Number of active users
* Number of translations submitted

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

import datetime
from pontoon.base.models import *
from django.db.models.functions import TruncMonth

data = {}

# New User Registrations
users = User.objects.all() \
    .annotate(period=TruncMonth('date_joined')) \
    .values('period') \
    .annotate(count=Count('id')) \
    .order_by('period')
for x in users:
    period = '{}-{:02d}'.format(x['period'].year, x['period'].month)
    if not period in data:
        data[period] = {}
    data[period]['registrations'] = x['count']

# Active Users
translations = Translation.objects.filter(user__isnull=False) \
    .annotate(period=TruncMonth("date")) \
    .values("period", "user_id") \
    .annotate(count=Count("user_id")) \
    .values('period', 'count') \
    .order_by("period")

translations_dict = defaultdict(list)
for x in translations:
    translations_dict[x["period"]].append(x["count"])

for y in translations_dict.items():
    period = '{}-{:02d}'.format(y[0].year, y[0].month)
    if not period in data:
        data[period] = {}
    data[period]['active'] = len(y[1])

# New Translation Submissions
translations = Translation.objects.filter(user__isnull=False) \
    .annotate(period=TruncMonth('date')) \
    .values('period') \
    .annotate(count=Count('id')) \
    .order_by('period')
for x in translations:
    period = '{}-{:02d}'.format(x['period'].year, x['period'].month)
    if not period in data:
        data[period] = {}
    data[period]['translations'] = x['count']

# Generate output
output = []
output.append('Period,New User Registrations,Active Users,Translations Submitted')
periods = list(data.keys())
periods.sort()
for period in periods:
    period_data = data[period]
    registrations = period_data['registrations'] if 'registrations' in period_data else 0
    active = period_data['active'] if 'active' in period_data else 0
    translations = period_data['translations'] if 'translations' in period_data else 0
    output.append('{},{},{},{}'.format(
        period,
        registrations,
        active,
        translations,
    ))

# Print output
print('\n'.join(output))
