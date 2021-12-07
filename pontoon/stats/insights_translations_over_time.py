from datetime import datetime
from pontoon.base.models import Project
from pontoon.insights.utils import get_insights

totals = {
  "months": {},
  "years": {},
  "projects": {},
}

for project in Project.objects.all():
    ins = get_insights(project=project)
    ht = ins["translation_activity"]["human_translations"]
    mt = ins["translation_activity"]["machinery_translations"]
    for i in range(len(ins["dates"])):
      sum = ht[i] + mt[i]
      if sum > 0:
        month = datetime.utcfromtimestamp(ins["dates"][i]/1000).strftime('%Y-%m')
        y, m = month.split("-")
        if month in totals["months"]:
          totals["months"][month] += sum
        else:
          totals["months"][month] = sum
        if y in totals["years"]:
          totals["years"][y] += sum
        else:
          totals["years"][y] = sum
        if project in totals["projects"]:
          totals["projects"][project] += sum
        else:
          totals["projects"][project] = sum

for y, y_data in totals["years"].items():
  print(f"Total for {y}: {y_data}")

for p, p_data in totals["projects"].items():
  print(f"Total for {p}: {p_data}")
