import argparse
import csv
from collections import Counter
from pathlib import Path


DEFAULT_INPUT = Path(__file__).with_name("masterList.csv")
DEFAULT_OUTPUT = Path(__file__).with_name("occupations.csv")


def analyze(masterlist_path: Path, output_path: Path) -> None:
    occupation_counts: Counter[str] = Counter()

    with masterlist_path.open("r", newline="", encoding="utf-8-sig") as masterlist:
        reader = csv.DictReader(masterlist, delimiter=";")
        if reader.fieldnames is None or "occupation" not in reader.fieldnames:
            raise ValueError("The input CSV must contain an 'occupation' column.")

        for row in reader:
            occupations = row["occupation"]
            if occupations:
                occupation_counts.update(
                    occupation.strip()
                    for occupation in occupations.split(",")
                    if occupation.strip()
                )

    total_occurrences = sum(occupation_counts.values())
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["Occupation", "Occurrences", "PercentageTotal"])
        for occupation, count in sorted(
            occupation_counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        ):
            percentage = count * 100 / total_occurrences if total_occurrences else 0
            writer.writerow([occupation, count, f"{percentage:.6f}"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count occupations in a master list CSV."
    )
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    analyze(args.input, args.output)
    print(f"Occupation counts saved to {args.output}")


if __name__ == "__main__":
    main()