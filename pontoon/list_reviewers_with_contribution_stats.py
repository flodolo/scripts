"""
Retrieve a list of reviewers for given locales and timeframe with a number of
suggestions they approved or rejected.
Self-reviewed translations are excluded from calculation.

Output is formatted as CSV with the following columns:
* Locale
* User
* Number of approved suggestions
* Number of rejected suggestions
* Total number of reviews
* Total number of submitted translations
* Ratio of submitted translations to reviews

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
# Use empty list for all locales
LOCALES = [
    #'it', 'ja', 'pl', 'ru', 'zh-CN',
]
START_DATE = "23/02/2019"  # DD/MM/YYYY
END_DATE = "23/02/2020"  # DD/MM/YYYY


# Script
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Q
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, Translation
from pontoon.contributors.utils import users_with_translations_counts


def get_ratio(translations, reviews):
    try:
        return format(float(translations) / (translations + reviews), ".2f")
    except ZeroDivisionError:
        return "-1"


locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, "%d/%m/%Y"))
end_date = tz.localize(datetime.strptime(END_DATE, "%d/%m/%Y"))

output = []
output.append(
    "Locale,User,Role,Number of Approved Suggestions,Number of Rejected Suggestions,Total Reviews,Translations,Ratio Submitted/Reviewed"
)

for locale in locales:
    users = {}
    # Translations submitted in Pontoon for given locale and timeframe
    translations = Translation.objects.filter(
        locale=locale,
        date__gte=start_date,
        date__lte=end_date,
    )
    # Above translations that have been approved, but not self-approved
    approved = translations.filter(approved_user__isnull=False).exclude(
        user=F("approved_user")
    )
    approved_users = User.objects.filter(
        pk__in=approved.values_list("approved_user", flat=True).distinct()
    )
    for user in approved_users:
        # Replace comma in role, e.g. "Manager for bn, bn-BD" to avoid breaking CSV
        role = user.role().replace(",", "+")
        users[user.email] = {
            "role": role,
            "approved": approved.filter(approved_user=user).count(),
            "rejected": 0,
        }
    # Above translations that have been rejected, but not self-rejected
    rejected = translations.filter(rejected_user__isnull=False).exclude(
        user=F("rejected_user")
    )
    rejected_users = User.objects.filter(
        pk__in=rejected.values_list("rejected_user", flat=True).distinct()
    )
    for user in rejected_users:
        if user.email in users:
            users[user.email]["rejected"] = rejected.filter(rejected_user=user).count()
        else:
            role = user.role().replace(",", "+")
            users[user.email] = {
                "role": role,
                "approved": 0,
                "rejected": rejected.filter(rejected_user=user).count(),
            }
    # Check other stats for contributors in this locale
    contributors = users_with_translations_counts(start_date, Q(locale=locale), None)
    for contributor in contributors:
        # Ignore users without reviews
        if contributor.email not in users:
            continue
        # Ignore "imported" strings
        if contributor.username == "Imported":
            continue
        users[contributor.email].update(
            {
                "translations_count": contributor.translations_count,
            }
        )
    for email, stats in users.items():
        total_reviews = stats["approved"] + stats["rejected"]
        total_translations = (
            stats["translations_count"] if "translations_count" in stats else 0
        )
        output.append(
            "{},{},{},{},{},{},{},{}".format(
                locale.code,
                email,
                stats["role"],
                stats["approved"],
                stats["rejected"],
                total_reviews,
                total_translations,
                get_ratio(total_translations, total_reviews),
            )
        )

print("\n".join(output))
