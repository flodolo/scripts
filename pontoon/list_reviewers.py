"""
Retrieve a list of reviewers for given locales and timeframe with a number of
suggestions they approved or rejected.
Self-reviewed translations are excluded from calculaton.

Output is formatted as CSV with the following columns:
* Locale
* User
* Number of Approved Suggestions
* Number of Rejected Suggestions

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
# Use empty list for all locales
LOCALES = [
    'ko',
    'my',
    'th',
]
START_DATE = '31/12/2018'  # DD/MM/YYYY
END_DATE = '11/04/2019'   # DD/MM/YYYY


# Script
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models import F
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, Translation

locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, '%d/%m/%Y'))
end_date = tz.localize(datetime.strptime(END_DATE, '%d/%m/%Y'))

output = []
output.append(
    'Locale,User,Number of Approved Suggestions,Number of Rejected Suggestions')

for locale in locales:
    users = {}
    # Translations submitted in Pontoon for given locale and timeframe
    translations = Translation.objects.filter(
        locale=locale,
        date__gte=start_date,
        date__lte=end_date,
    )
    # Above translations that have been approved, but not self-approved
    approved = (
        translations
        .filter(approved_user__isnull=False)
        .exclude(user=F('approved_user'))
    )
    approved_users = User.objects.filter(
        pk__in=approved.values_list('approved_user', flat=True).distinct()
    )
    for user in approved_users:
        users[user.email] = {
            'approved': approved.filter(approved_user=user).count(),
            'rejected': 0,
        }
    # Above translations that have been rejected, but not self-rejected
    rejected = (
        translations
        .filter(rejected_user__isnull=False)
        .exclude(user=F('rejected_user'))
    )
    rejected_users = User.objects.filter(
        pk__in=rejected.values_list('rejected_user', flat=True).distinct()
    )
    for user in rejected_users:
        if user.email in users:
            users[user.email]['rejected'] = rejected.filter(
                rejected_user=user).count()
        else:
            users[user.email] = {
                'approved': 0,
                'rejected': rejected.filter(rejected_user=user).count(),
            }
    for email, stats in users.items():
        output.append('{},{},{},{}'.format(
            locale.code,
            email,
            stats['approved'],
            stats['rejected'],
        ))

print('\n'.join(output))
