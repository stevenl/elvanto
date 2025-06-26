#!/usr/bin/env python3
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
# ---

# %% [markdown]
"""
Generates a graph using the attendance report from Elvanto.

You first need to download the report manually. Export it as a CSV file from:
```
https://{elvanto_host}/admin/reports/report_existing/?category=services&report=service_reports_individuals&date_range_type=this_year&date_range_from=20%2F11%2F2024&date_range_to=26%2F11%2F2024&frequency=&attendance=attended&did_not_attend_times=&attended_times=&service_types_services=y&service_type%5B%5D=6f3a9664-435f-42fe-a841-28c53b7bcd97&service_type%5B%5D=aacac264-aedc-418b-a8c2-6aca498bbca6&include_individual_service=yes&multi_select_filter_demographic%5B%5D=&multi_select_filter_columns%5B%5D=demo&columns%5B%5D=category_id&columns%5B%5D=demographic_id&sort=0&order=asc&output=web&export_orientation=l&export_size=&export_labels_address=
```

Usage:
```
./attendance.py -f path/to/Service-Individual-Attendance-1-Jan-2025-31-Dec-2025.csv
```

To keep the Jupyter Notebook in sync:
```
jupytext --set-formats ipynb,py attendance.py --sync
```
"""

# %%
import argparse
import datetime as dt
import matplotlib.pyplot as plt
import os
import pandas as pd
import re
import sys


# %% [markdown]
# Parse args
# ----------


# %%
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a graph from the Elvanto attendance report"
    )
    parser.add_argument(
        "-f", "--file", required=True, help="The CSV file from Elvanto to process"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        raise SystemExit(f"error: No such file exists: {args.file}")
    return args


# sys.argv = ["attendance.py", "-f", "data/Service-Individual-Attendance-2025-06-24.csv"]
args = parse_args()
args


# %% [markdown]
# Clean and normalize the attendance report
# -----------------------------------------
# * Unpivot the table so that each column representing the attendance for each
#   week is converted to a single column for attendance and another column to
#   indicate the service date.
# * Extract the date out of the service names and convert them to date objects.


# %%
def clean_and_normalize_attendance_report(csv_data: pd.DataFrame) -> pd.DataFrame:
    def service_name_to_date_str(column_name: str) -> str:
        dd_mm = re.search(r"(\d\d/\d\d)", column_name)
        return (
            f"{ dd_mm.group() }/{ dt.date.today().year }"
            if dd_mm != None  # Only convert column names that contain a date
            else column_name  # All other column names remain the same
        )

    data = csv_data.rename(columns=service_name_to_date_str)

    # Unpivot the date-attendance columns into rows.
    # The date column names become the values in a new Date column, and
    # the attendance values from the original date columns go in a new Attended column.
    id_columns = data.columns[:2]
    date_columns = data.columns[2:]
    individual_attendance = (
        data.melt(
            id_vars=id_columns,
            value_vars=date_columns,
            var_name="Date",
            value_name="Attended",
        )
        # Discard the non-attendance data
        .query("Attended == 'Y'").drop(columns="Attended")
    )

    # Convert date strings to date objects
    individual_attendance["Date"] = pd.to_datetime(
        individual_attendance["Date"], format="%d/%m/%Y"
    )

    return individual_attendance


print(f"Processing file: {args.file}")
csv_data = pd.read_csv(args.file).drop(
    columns=["First Name", "Last Name", "Attended", "Absent"]
)
individual_attendance = clean_and_normalize_attendance_report(csv_data)
individual_attendance


# %% [markdown]
# Create the attendance columns
# -----------------------------

# %%
individual_attendance["Total"] = True

individual_attendance.loc[
    individual_attendance["Demographics"] == "Adults", "Adults"
] = True

individual_attendance.loc[
    individual_attendance["People Category"].isin(
        ["Newcomers", "Visitors / New People"]
    ),
    "Newcomers/Visitors",
] = True

# We don't need this data anymore
individual_attendance.drop(
    columns=["People Category", "Demographics"],
    inplace=True,
)

individual_attendance


# %% [markdown]
# Summarise (aggregate) the data
# ------------------------------

# %%
# Each of the attendance columns will get their own count
attendance_summary = individual_attendance.groupby("Date").count()
attendance_summary


# %% [markdown]
# Generate the graph
# ------------------

# %%
attendance_summary.plot()
plt.grid()
plt.show()
