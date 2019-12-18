"""
Retrieve a list of self-approval ratios for given locales and timeframe,
calculated as share of translations approved without peer review.

Output is formatted as CSV with the following columns:
* Locale
* Self-Approval Ratio

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = [
    'it', 'ja', 'pl', 'ru', 'zh-CN',
]
START_DATE = '18/12/2018' # DD/MM/YYYY
END_DATE = '18/12/2019'   # DD/MM/YYYY


# Script
from __future__ import division
from datetime import datetime
from django.db.models import F
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, Translation

locales = Locale.objects.filter(code__in=LOCALES)
tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, '%d/%m/%Y'))
end_date = tz.localize(datetime.strptime(END_DATE, '%d/%m/%Y'))

output = []
output.append('Locale,Self-Approval Ratio')

for locale in locales:
    all_approved = Translation.objects.filter(
        locale=locale,
        date__gte=start_date,
        date__lte=end_date,
        approved=True,
    )
    self_approved = all_approved.filter(
        user=F('approved_user')
    )
    try:
        ratio = format(self_approved.count() / all_approved.count(), '.2f')
    except ZeroDivisionError:
        ratio = '-1'
    output.append('{},{}'.format(
        locale.code,
        ratio,
    ))

print('\n'.join(output))
