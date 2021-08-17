"""
Check tags in Firefox that are in more than one tag.

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

from pontoon.base.models import *
from pontoon.tags.models import *

for resource in Resource.objects.filter(project__slug="firefox"):
    tags = Tag.objects.filter(resources__in=[resource])
    if tags.count() != 1:
        resource
        tags.values_list("slug", flat=True)
