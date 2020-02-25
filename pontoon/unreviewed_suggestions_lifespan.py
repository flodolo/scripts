"""
Retrieve a list of average unreviewed suggestions lifespans for given locales
and timeframe. Self-approved translations are excluded from calculaton.

Output is formatted as CSV with the following columns:
* Locale
* Average Unreviewed Suggestion Lifespan

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
# Use empty list for all locales
LOCALES = [
    #'it'
]
START_DATE = '23/02/2019'  # DD/MM/YYYY
END_DATE = '23/02/2020'   # DD/MM/YYYY
# If True, prettify the output (e.g. "40 days 15:21:23").
# If False, display days and round to 2 decimals.
PRETTY_OUTPUT = True

# Script
from datetime import datetime, timedelta
from django.db.models import Avg, F
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, Translation

locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, '%d/%m/%Y'))
end_date = tz.localize(datetime.strptime(END_DATE, '%d/%m/%Y'))

output = []
output.append('Locale,Average Unreviewed Suggestion Lifespan')

def divide_timedelta(td, divisor):
    total_seconds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6
    divided_seconds = round(total_seconds / float(divisor))
    days = round(divided_seconds / 86400, 2)
    return timedelta(seconds=divided_seconds) if PRETTY_OUTPUT else days

for locale in locales:
    # Translations submitted in Pontoon for given locale and timeframe
    translations = Translation.objects.filter(
        user__isnull=False,
        locale=locale,
        date__gte=start_date,
        date__lte=end_date,
    )
    # Above translations that have been approved, but not self-approved
    approved = (
        translations
        .filter(approved_date__isnull=False)
        .exclude(user=F('approved_user'))
    )
    # Above translations that have been rejected, but not self-rejected
    rejected = (
        translations
        .filter(rejected_date__isnull=False)
        .exclude(user=F('rejected_user'))
    )
    approved_delta = (
        approved.aggregate(
            average_delta=Avg(
                F('approved_date') - F('date')
            )
        )
    )['average_delta']
    rejected_delta = (
        rejected.aggregate(
            average_delta=Avg(
                F('rejected_date') - F('date')
            )
        )
    )['average_delta']
    try:
        combined_delta = divide_timedelta(approved_delta + rejected_delta, 2)
    except TypeError:
        combined_delta = 0
    output.append('{},{}'.format(
        locale.code,
        str(combined_delta).replace(',', ''),
    ))

print('\n'.join(output))
