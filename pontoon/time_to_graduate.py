"""
Retrieve times to graduate to a new role for translators and managers
of a given locale.

Output is formatted as CSV with the following columns:
* Locale
* User
* Date
* New Role
* Days in Previous Role

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
# Use empty list for all locales
LOCALES = [
    'it', 'ja', 'pl', 'ru', 'zh-CN',
]
START_DATE = '01/01/2010'  # DD/MM/YYYY
# Set to True to ignore duplicates
IGNORE_DUPLICATES = False

# Script
from datetime import datetime
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, PermissionChangelog

locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, '%d/%m/%Y'))
logs = PermissionChangelog.objects.filter(
    action_type='added',
    created_at__gte=start_date,
)

output = []
output.append('Locale,User,Date,New Role,Days in Previous Role')

for locale in locales:
    # Use group__name__iexact to only get promotions to full translator and
    # ignore promotion to project translator.
    recorded_hashes = []
    for log in logs.filter(group__name__endswith=locale.code + ' translators'):
        user = log.performed_on
        row_data = (
            locale.code,
            user.email,
            log.created_at.date(),
            log.group.name,
            (log.created_at - user.date_joined).days,
        )
        if IGNORE_DUPLICATES:
            action_hash = hash(row_data)
            if action_hash not in recorded_hashes:
                output.append('{},{},{},{},{}'.format(*row_data))
                recorded_hashes.append(action_hash)
        else:
            output.append('{},{},{},{},{}'.format(*row_data))
    for log in logs.filter(group=locale.managers_group):
        user = log.performed_on
        try:
            user_translator_log = logs.filter(
                performed_on=user, group=locale.translators_group).latest('created_at')
            # User was never a translator
            if not user_translator_log:
                date_previous = user.date_joined
            # We don't know
            elif log.created_at < user_translator_log.created_at:
                continue
            else:
                date_previous = user_translator_log.created_at
            row_data = (
                locale.code,
                user.email,
                log.created_at.date(),
                log.group.name,
                (log.created_at - date_previous).days,
            )
            if IGNORE_DUPLICATES:
                action_hash = hash(row_data)
                if action_hash not in recorded_hashes:
                    output.append('{},{},{},{},{}'.format(*row_data))
                    recorded_hashes.append(action_hash)
                else:
                    output.append('{},{},{},{},{}'.format(*row_data))
        except PermissionChangelog.DoesNotExist:
            pass

print('\n'.join(output))
