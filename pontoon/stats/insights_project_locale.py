"""
Insights for given project and locale.

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

from pontoon.insights.models import ProjectLocaleInsightsSnapshot

project = "mozilla-vpn-client"
locale = "de"

projects = ProjectLocaleInsightsSnapshot.objects.filter(
    project_locale__project__slug=project, project_locale__locale__code=locale
).order_by("created_at")

output = ["Date,Completion,Total,Approved,Fuzzy,Errors,Warnings,Unreviewed"]
for p in projects:
    output.append(
        "{},{},{},{},{},{},{},{}".format(
            p.created_at,
            p.completion,
            p.total_strings,
            p.approved_strings,
            p.fuzzy_strings,
            p.strings_with_errors,
            p.strings_with_warnings,
            p.unreviewed_strings,
        )
    )

print("\n".join(output))
