"""
Retrieve a list of active contributors for given locales, timeframe and roles.

Output is formatted as CSV with the following columns:
* locale
* date_joined
* profile_url
* user_role
* total_submission_count
* approved_count
* rejected_count
* unreviewed_count
* approved_rejected_ratio

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
# Use empty list for all locales
LOCALES = [
    #'it', 'ja', 'pl', 'ru', 'zh-CN',
]
MONTHS_AGO = 18
ROLES = [
    # 'admin',
    # 'contributor',
    'manager',
    # 'translator',
]


# Script
from __future__ import division
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pontoon.base.models import Locale
from pontoon.contributors.utils import users_with_translations_counts

locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

start_date = (timezone.now() + relativedelta(months=-MONTHS_AGO))

def get_profile(username):
    from urllib.parse import urljoin
    return urljoin(
        settings.SITE_URL,
        reverse(
            'pontoon.contributors.contributor.username',
            args=[username]
        )
    )

def get_ratio(approved, rejected):
    try:
        return format(approved / (approved + rejected), '.2f')
    except ZeroDivisionError:
        return '-1'

output = []
output.append('Locale,Date Joined,Profile URL,Role,Translations,Approved,Rejected,Pending,Ratio')
for locale in locales:
    contributors = users_with_translations_counts(start_date, Q(locale=locale), None)
    for contributor in contributors:
        role = contributor.locale_role(locale)
        if role not in ROLES:
            continue
        # Ignore "imported" strings
        if contributor.username == 'Imported':
            continue
        output.append('{},{},{},{},{},{},{},{},{}'.format(
            locale.code,
            contributor.date_joined.date(),
            get_profile(contributor.username),
            role,
            contributor.translations_count,
            contributor.translations_approved_count,
            contributor.translations_rejected_count,
            contributor.translations_unapproved_count,
            get_ratio(contributor.translations_approved_count, contributor.translations_rejected_count)
        ))

print('\n'.join(output))
