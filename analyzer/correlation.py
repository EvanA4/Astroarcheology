#!/usr/bin/env python3
import argparse
import csv
from scipy.stats import chisquare


def main():
    parser = argparse.ArgumentParser(
        description="Run a chi-squared goodness-of-fit test on a CSV row."
    )
    parser.add_argument("csv_path", help="Path to the CSV file")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

    # The first column is the profession; the rest are observed counts.
    observed = [float(value) for value in row[1:]]
    if len(observed) != len(header) - 1:
        raise ValueError("The data row must have a count for each zodiac-sign column.")
    if any(value < 0 for value in observed):
        raise ValueError("Counts cannot be negative.")

    result = chisquare(observed)
    dof = len(observed) - 1

    print(f"DOF: {dof}")
    print(f"Chi-squared: {result.statistic:.6g}")
    print(f"P-value: {result.pvalue:.6g}")


if __name__ == "__main__":
    main()
