#! /usr/bin/env python3

import argparse
import csv
import datetime

cl_parser = argparse.ArgumentParser()
cl_parser.add_argument("csv_path", help="Path to CSV file")
args = cl_parser.parse_args()


data = {}
with open(args.csv_path) as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
        locale = row["Locale"]
        if locale not in data:
            data[locale] = []
        days_from_login = (
            datetime.datetime.today()
            - datetime.datetime.strptime(row["Last Login"], "%Y-%m-%d")
        ).days
        days_from_activity = (
            -1
            if row["Last Activity"] == "No activity yet"
            else (
                datetime.datetime.today()
                - datetime.datetime.strptime(row["Last Activity"], "%Y-%m-%d")
            ).days
        )
        data[locale].append(
            {
                "profile": row["Profile URL"],
                "days_from_login": days_from_login,
                "days_from_activity": days_from_activity,
            }
        )

inactive = 0
never_active = 0
inactivity_days = 180
abandoned_locales = []
for locale, managers in data.items():
    locale_never_active = locale_inactive = 0
    for manager in managers:
        if manager["days_from_activity"] == -1:
            locale_never_active += 1
        # Use days_from_activity to consider the last activity
        if manager["days_from_login"] >= inactivity_days:
            locale_inactive += 1

    never_active += locale_never_active
    inactive += locale_inactive

    if (len(managers) - locale_never_active - locale_inactive) == 0:
        abandoned_locales.append(locale)
abandoned_locales.sort()

print("Number of locales: {}".format(len(data.keys())))
print("Number of managers never active: {}".format(never_active))
print(
    "Number of managers who have not logged in for more than {} days: {}".format(
        inactivity_days, inactive
    )
)
print("Locales with no manager ({}):".format(len(abandoned_locales)))
print("\n".join(abandoned_locales))
