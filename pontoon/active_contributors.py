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
    'ace', 'ach', 'af', 'an', 'anp', 'ar', 'as', 'ast', 'az', 'ban', 'be', 'bg',
    'bn', 'bo', 'br', 'brx', 'bs', 'ca', 'ca-valencia', 'cak', 'ceb', 'ckb', 'co',
    'crh', 'cs', 'cy', 'da', 'de', 'dsb', 'el', 'en-CA', 'en-GB', 'eo', 'es',
    'es-AR', 'es-CL', 'es-ES', 'es-MX', 'et', 'eu', 'fa', 'ff', 'fi', 'fr', 'frp',
    'fur', 'fy-NL', 'ga-IE', 'gd', 'gl', 'gn', 'gu-IN', 'gv', 'he', 'hi-IN', 'hil',
    'hr', 'hsb', 'hu', 'hy-AM', 'hye', 'ia', 'id', 'ilo', 'is', 'it', 'ixl', 'ja',
    'jv', 'ka', 'kab', 'kk', 'km', 'kmr', 'kn', 'ko', 'ks', 'lb', 'lg', 'lij',
    'lo', 'lt', 'ltg', 'lv', 'mai', 'meh', 'mix', 'mk', 'ml', 'mr', 'ms', 'my',
    'nb-NO', 'ne-NP', 'nl', 'nn-NO', 'nv', 'ny', 'oc', 'or', 'pa-IN', 'pai', 'pl',
    'ppl', 'pt-BR', 'pt-PT', 'quy', 'qvi', 'rm', 'ro', 'ru', 'sat', 'sc', 'scn',
    'sco', 'ses', 'si', 'sk', 'sl', 'son', 'sq', 'sr', 'su', 'sv-SE', 'sw', 'szl',
    'ta', 'te', 'tg', 'th', 'tl', 'tr', 'trs', 'tsz', 'tt', 'tzm', 'uk', 'ur',
    'uz', 'vec', 'vi', 'wo', 'xcl', 'xh', 'yo', 'zam', 'zgh', 'zh-CN', 'zh-TW'
]
MONTHS_AGO = 6
ROLES = [
    # 'admin',
    # 'contributor',
    "manager",
    'translator',
]


# Script
from __future__ import division
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pontoon.base.models import Locale
from pontoon.base.models import Locale, Translation
from pontoon.contributors.utils import users_with_translations_counts

locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

start_date = timezone.now() + relativedelta(months=-MONTHS_AGO)


def get_profile(username):
    from urllib.parse import urljoin
    return urljoin(
        settings.SITE_URL,
        reverse("pontoon.contributors.contributor.username", args=[username]),
    )


def get_ratio(approved, rejected):
    try:
        return format(approved / (approved + rejected), ".2f")
    except ZeroDivisionError:
        return "-1"


def get_latest_activity(user):
    translations = Translation.objects.filter(Q(user=user) | Q(approved_user=user))
    if not translations.exists():
        return "No activity yet"
    translated = translations.latest("date").date
    approved = translations.latest("approved_date").approved_date
    activities = []
    if translated:
        activities.append(translated)
    if approved:
        activities.append(approved)
    activities.sort()
    return activities[-1].date() if len(activities) > 0 else None


output = []
output.append(
    "Locale,Date Joined,Latest Activity,Profile URL,Role,Translations,Approved,Rejected,Pending,Ratio"
)
for locale in locales:
    contributors = users_with_translations_counts(start_date, Q(locale=locale), None)
    for contributor in contributors:
        role = contributor.locale_role(locale)
        if role not in ROLES:
            continue
        # Ignore "imported" strings
        if contributor.username == "Imported":
            continue
        output.append(
            "{},{},{},{},{},{},{},{},{},{}".format(
                locale.code,
                contributor.date_joined.date(),
                get_latest_activity(contributor),
                get_profile(contributor.username),
                role,
                contributor.translations_count,
                contributor.translations_approved_count,
                contributor.translations_rejected_count,
                contributor.translations_unapproved_count,
                get_ratio(
                    contributor.translations_approved_count,
                    contributor.translations_rejected_count,
                ),
            )
        )

print("\n".join(output))
