"""
Retrieve times to graduate to a new role for translators and managers
of a given locale.

Output is formatted as CSV with the following columns:
* Locale
* User
* New Role
* Time in Previous Role

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = ['gn', 'ace', 'tt', 'ppl', 'is']


# Script
from pontoon.base.models import Locale, PermissionChangelog

locales = Locale.objects.filter(code__in=LOCALES)
logs = PermissionChangelog.objects.filter(action_type='added')

output = []
output.append('Locale,User,New Role,Time in Previous Role')

for locale in locales:
    for log in logs.filter(group__name__endswith=locale.code + ' translators'):
        user = log.performed_on
        output.append('{},{},{},{}'.format(
            locale.code,
            user.email,
            log.group.name,
            (log.created_at - user.date_joined),
        ))
    for log in logs.filter(group=locale.managers_group):
        user = log.performed_on
        try:
            user_translator_log = logs.filter(performed_on=user, group=locale.translators_group).last()
            if not user_translator_log:
                continue
            output.append('{},{},{},{}'.format(
                locale.code,
                user.email,
                log.group.name,
                (log.created_at - user_translator_log.created_at),
            ))
        except PermissionChangelog.DoesNotExist:
            pass

print('\n'.join(output))
