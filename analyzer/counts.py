#!/usr/bin/env python3
import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime

from zodiac import zodiac_sign, ZODIAC_SIGNS


def count_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as csv_file:
        return sum(1 for _ in csv.DictReader(csv_file, delimiter=";"))


def main():
    parser = argparse.ArgumentParser(
        description="Count tropical zodiac signs for each profession."
    )
    parser.add_argument("input_csv", help="Path to the semicolon-delimited input CSV")
    parser.add_argument("output_csv", help="Path for the output CSV")
    args = parser.parse_args()

    total_rows = count_rows(args.input_csv)
    counts = defaultdict(Counter)

    with open(args.input_csv, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")

        for processed, row in enumerate(reader, start=1):
            try:
                birthdate = datetime.fromisoformat(row["birthdate"].strip())
            except (KeyError, AttributeError, ValueError):
                birthdate = None

            if birthdate is not None:
                try:
                    sign = zodiac_sign(birthdate)
                except Exception:
                    sign = None

                if sign is not None:
                    for profession in row.get("occupation", "").split(","):
                        profession = profession.strip()
                        if profession:
                            counts[profession][sign] += 1

            if processed % 1_000 == 0:
                percentage = processed / total_rows * 100 if total_rows else 100
                print(
                    f"\rProgress: {percentage:6.2f}% ({processed}/{total_rows} rows)",
                    end="",
                    file=sys.stderr,
                    flush=True,
                )

    print(file=sys.stderr)  # Finish the progress line.

    with open(args.output_csv, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["profession", *ZODIAC_SIGNS])

        for profession in sorted(counts):
            sign_counts = counts[profession]
            if all(sign_counts[sign] >= 5 for sign in ZODIAC_SIGNS):
                writer.writerow(
                    [profession, *(sign_counts[sign] for sign in ZODIAC_SIGNS)]
                )


if __name__ == "__main__":
    main()
