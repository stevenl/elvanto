#!/usr/bin/env python

import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re


def main():
    args = parse_args()

    # Export CSV report from:
    # https://{elvanto_host}/admin/reports/report_existing/?category=services&report=service_reports_individuals&date_range_type=this_year&date_range_from=20%2F11%2F2024&date_range_to=26%2F11%2F2024&frequency=&attendance=attended&did_not_attend_times=&attended_times=&service_types_services=y&service_type%5B%5D=6f3a9664-435f-42fe-a841-28c53b7bcd97&service_type%5B%5D=aacac264-aedc-418b-a8c2-6aca498bbca6&include_individual_service=yes&multi_select_filter_demographic%5B%5D=&multi_select_filter_columns%5B%5D=demo&columns%5B%5D=category_id&columns%5B%5D=demographic_id&sort=0&order=asc&output=web&export_orientation=l&export_size=&export_labels_address=
    print(f"Processing file: {args.file}")
    csv_data = pd.read_csv(args.file)
    individual_attendance = preprocess_individual_attendance_data(csv_data)

    # Create attendance columns
    individual_attendance["Total"] = "Y"
    individual_attendance.loc[
        individual_attendance["Demographics"].eq("Adults"), "Adults"
    ] = "Y"
    individual_attendance.loc[
        individual_attendance["People Category"].isin(
            ["Newcomers", "Visitors / New People"]
        ),
        "Newcomers/Visitors",
    ] = "Y"

    individual_attendance.drop(
        columns=["First Name", "Last Name", "People Category", "Demographics"],
        inplace=True,
    )

    generate_report(individual_attendance)


def parse_args():
    parser = argparse.ArgumentParser(description="Process the Elvanto attendance data")
    parser.add_argument("-f", "--file", help="The name of the file to process.")
    return parser.parse_args()


def preprocess_individual_attendance_data(csv_data: pd.DataFrame) -> pd.DataFrame:
    def extract_date(col: str) -> str:
        dd_mm = re.search(r"(\d\d/\d\d)", col)
        return dd_mm.group() + "/2025" if dd_mm != None else col

    def remove_spaces(col: str) -> str:
        return col.replace(" ", "")

    data = csv_data.drop(columns=["Attended", "Absent"]).rename(columns=extract_date)
    # .rename(columns=remove_spaces)

    # Unpivot the service date attendance columns into rows
    id_columns = data.columns[:4]
    date_columns = data.columns[4:]
    individual_attendance = (
        data.melt(
            id_vars=id_columns,
            value_vars=date_columns,
            var_name="Date",
            value_name="Attended",
        )
        .query("Attended == 'Y'")
        .drop(columns="Attended")
    )

    # Convert date strings to date objects
    individual_attendance["Date"] = pd.to_datetime(
        individual_attendance["Date"], format="%d/%m/%Y"
    )

    return individual_attendance


def generate_report(individual_attendance: pd.DataFrame):
    attendance_report = individual_attendance.groupby("Date").count()

    # Generate the graph
    attendance_report.plot()
    plt.grid()
    plt.show()


if __name__ == "__main__":
    main()
