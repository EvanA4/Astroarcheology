#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path

COLUMNS = ["wikidata_code", "name", "birthdate", "occupation"]


def merge_csvs(directory: Path) -> None:
    output_file = directory / "merged.csv"
    rows = []

    for csv_file in sorted(directory.glob("*.csv")):
        if csv_file == output_file:
            continue

        with csv_file.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                cleaned_row = {
                    column: row.get(column, "") for column in COLUMNS
                }
                cleaned_row["occupation"] = re.sub(
                    r",\s+", ",", cleaned_row["occupation"]
                )
                rows.append(cleaned_row)

    rows.sort(key=lambda row: row["name"].casefold())

    with output_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=COLUMNS, delimiter=";", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Merged {len(rows)} rows into {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge semicolon-separated CSV files in a directory."
    )
    parser.add_argument("directory", type=Path, help="Directory containing CSV files")
    args = parser.parse_args()

    if not args.directory.is_dir():
        parser.error(f"Not a directory: {args.directory}")

    merge_csvs(args.directory)


if __name__ == "__main__":
    main()
