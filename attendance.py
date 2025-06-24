#!/usr/bin/env python3

"""
Generates a graph using the attendance report from Elvanto

You first need to download the report manually. Export it as a CSV file from:
https://{elvanto_host}/admin/reports/report_existing/?category=services&report=service_reports_individuals&date_range_type=this_year&date_range_from=20%2F11%2F2024&date_range_to=26%2F11%2F2024&frequency=&attendance=attended&did_not_attend_times=&attended_times=&service_types_services=y&service_type%5B%5D=6f3a9664-435f-42fe-a841-28c53b7bcd97&service_type%5B%5D=aacac264-aedc-418b-a8c2-6aca498bbca6&include_individual_service=yes&multi_select_filter_demographic%5B%5D=&multi_select_filter_columns%5B%5D=demo&columns%5B%5D=category_id&columns%5B%5D=demographic_id&sort=0&order=asc&output=web&export_orientation=l&export_size=&export_labels_address=

Usage:
    ./attendance.py -f path/to/Service-Individual-Attendance-1-Jan-2025-31-Dec-2025.csv

"""

import argparse
import datetime as dt
import matplotlib.pyplot as plt
import os
import pandas as pd
import re


def main():
    args = parse_args()

    print(f"Processing file: {args.file}")
    csv_data = pd.read_csv(args.file)
    individual_attendance = preprocess_individual_attendance_data(csv_data)

    # Create attendance columns
    individual_attendance["Total"] = True

    individual_attendance.loc[
        individual_attendance["Demographics"].eq("Adults"), "Adults"
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

    # Each of the attendance columns will get their own count
    attendance_summary = individual_attendance.groupby("Date").count()

    print(attendance_summary)
    generate_graph(attendance_summary)


def parse_args():
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


def preprocess_individual_attendance_data(csv_data: pd.DataFrame) -> pd.DataFrame:
    def to_date_str(column_name: str) -> str:
        dd_mm = re.search(r"(\d\d/\d\d)", column_name)
        return (
            f"{ dd_mm.group() }/{ dt.date.today().year }"
            if dd_mm != None  # Only convert column names that contain a date
            else column_name  # All other column names remain the same
        )

    data = csv_data.drop(
        columns=["First Name", "Last Name", "Attended", "Absent"]
    ).rename(columns=to_date_str)

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


def generate_graph(attendance_summary: pd.DataFrame):
    attendance_summary.plot()
    plt.grid()
    plt.show()


if __name__ == "__main__":
    main()
