import pandas as pd
from zodiac import zodiac_sign, ZODIAC_SIGNS
from datetime import datetime
from sys import argv
import os


EXAMPLE_PATH = "example.csv"


def analyze(csv_path: str):
    # create directory for computed CSVs
    if not os.path.exists("output"):
        os.mkdir("output")

    # read CSV and compute actual zodiac signs
    df = pd.read_csv(csv_path)
    birthdays = df["birthdate"].tolist()
    actual_zodiacs = [zodiac_sign(datetime.fromisoformat(birthday)) for birthday in birthdays]
    df["zodiac"] = actual_zodiacs
    df.to_csv(os.path.join("output", "people.csv"), index=False)

    # categorize into professions
    df_cols = ["profession"] + list(ZODIAC_SIGNS)
    professions_df = pd.DataFrame(columns=df_cols)
    professions = df["profession"].unique().tolist()
    for profession in professions:
        tmp_df = df[df["profession"] == profession]
        sign_counts = tmp_df["zodiac"].value_counts().to_dict()
        row_data = [profession] + [sign_counts[sign] if sign in sign_counts else 0 for sign in ZODIAC_SIGNS]
        professions_df.loc[len(professions_df)] = row_data
    professions_df.to_csv(os.path.join("output", "professions.csv"), index=False)

if __name__ == "__main__":
    if len(argv) > 2:
        print("usage: analyze.py <CSV file>")
        exit(-1)

    if len(argv) == 2:
        if not os.path.isfile(argv[1]):
            print("Error: CSV file does not exist.")
            exit(-1)
        print(f"Analyzing {argv[1]}...", end='\r')
        analyze(argv[1])
        print(f"Analyzing {argv[1]}...done")
    else:
        print("No CSV file specified, running demo...")
        analyze(EXAMPLE_PATH)
