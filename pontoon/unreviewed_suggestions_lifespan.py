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
LOCALES = ['ko', 'my', 'th', 'tl', 'vi']
START_DATE = '31/12/2018' # DD/MM/YYYY
END_DATE = '11/04/2019'   # DD/MM/YYYY


# Script
from datetime import datetime
from django.db.models import Avg, F
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, Translation

locales = Locale.objects.filter(code__in=LOCALES)
tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, '%d/%m/%Y'))
end_date = tz.localize(datetime.strptime(END_DATE, '%d/%m/%Y'))

output = []
output.append('Locale,Average Unreviewed Suggestion Lifespan')

for locale in locales:
    translations = Translation.objects.filter(
        locale=locale,
        date__gte=start_date,
        date__lte=end_date,
    ).exclude(
        user=F('approved_user'),
    ).aggregate(
        average_delta=Avg(
            F('approved_date') - F('date')
        )
    )
    output.append('{},{}'.format(
        locale.code,
        str(translations['average_delta']).replace(',', ''),
    ))

print('\n'.join(output))
