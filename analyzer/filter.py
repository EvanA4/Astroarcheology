#!/usr/bin/env python3
import argparse
import csv


def filter_csv(input_path, output_path):
    # Count distinct people for each profession.
    people_by_profession = {}

    with open(input_path, "r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile, delimiter=";")
        for row in reader:
            for profession in row["occupation"].split(","):
                profession = profession.strip()
                if profession:
                    people_by_profession.setdefault(profession, set()).add(
                        row["wikidata_code"]
                    )

    # Keep only professions associated with at least 60 people.
    common_professions = {
        profession
        for profession, people in people_by_profession.items()
        if len(people) >= 60
    }

    with open(input_path, "r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile, delimiter=";")
        fieldnames = reader.fieldnames

        if fieldnames is None:
            raise ValueError("The input CSV is empty or has no header.")
        if "birthdate" not in fieldnames:
            raise ValueError("The input CSV must have a 'birthdate' column.")

        rows = []
        for row in reader:
            professions = [
                profession.strip()
                for profession in row["occupation"].split(",")
                if profession.strip() in common_professions
            ]

            if professions:
                row["occupation"] = ",".join(professions)
                rows.append(row)

    # ISO-format dates sort chronologically as strings; blank dates go last.
    rows.sort(key=lambda row: (not row["birthdate"], row["birthdate"]))

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter professions and sort the output by birthdate."
    )
    parser.add_argument("input_path", help="Path to the input CSV")
    parser.add_argument("output_path", help="Path for the filtered CSV")
    args = parser.parse_args()

    filter_csv(args.input_path, args.output_path)
