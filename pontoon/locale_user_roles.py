"""
Retrieve a list of users for given locales and role.

Output is formatted as CSV with the following columns:
* Role
* Locale
* Profile URL
* Date Joined
* Last Login
* Last Activity

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = [
    # 'de',
    # 'fr',
    # 'it',
]

ROLE = 'manager'  # Possible values: 'manager', 'translator', 'contributor'


# Script
from collections import defaultdict
from django.db.models import Q, Prefetch
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from pontoon.base.models import Locale, Translation
from pontoon.contributors.utils import users_with_translations_counts

# Get latest activity of the user


def get_latests_activity(user):
    translations = Translation.objects.filter(
        Q(user=user) | Q(approved_user=user))
    if not translations.exists():
        return "No activity yet"
    translated = translations.latest('date').date
    approved = translations.latest('approved_date').approved_date
    activities = []
    if translated:
        activities.append(translated)
    if approved:
        activities.append(approved)
    activities.sort()
    return activities[-1].date() if len(activities) > 0 else None

# Generate Profile URL


def get_profile(username):
    from urllib.parse import urljoin
    return urljoin(
        settings.SITE_URL,
        reverse(
            'pontoon.contributors.contributor.username',
            args=[username]
        )
    )


output = []
output.append('Role,Locale,Profile URL,Email,Date Joined,Last Login,Last Activity')

locales = Locale.objects.available()
if len(LOCALES) > 0:
    locales = locales.filter(code__in=LOCALES)

for locale in locales:
    if ROLE == 'manager':
        users = locale.managers_group.user_set.all()
    elif ROLE == 'translator':
        users = locale.translators_group.user_set.all()
    else:
        users = users_with_translations_counts(None, Q(locale=locale), None)
        ROLE = 'contributor'
    for user in users:
        output.append('{},{},{},{},{},{},{}'.format(
            ROLE,
            locale.code,
            get_profile(user.username),
            user.email,
            user.date_joined.date(),
            user.last_login.date(),
            get_latests_activity(user),
        ))

print('\n'.join(output))
