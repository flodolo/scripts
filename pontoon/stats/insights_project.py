"""
Insights for given project.

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

from pontoon.insights.models import ProjectInsightsSnapshot

project = "mozilla-vpn-client"

projects = ProjectInsightsSnapshot.objects.filter(project__slug=project).order_by(
    "created_at"
)

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
