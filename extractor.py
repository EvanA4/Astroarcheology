import csv
import os
import re
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
BATCH_SIZE = 50
PAUSE_SECONDS = 2

HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "PeopleDataExtractor/1.0 (contact: your-email@example.org)",
}

FIELDNAMES = ["wikidata_code", "name", "birthdate", "occupation"]


def get_qids(csv_path):
    """Read unique Wikidata QIDs from the wikidata_code column."""
    qids = set()

    with open(csv_path, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "wikidata_code" not in reader.fieldnames:
            raise ValueError("Input CSV must have a 'wikidata_code' column.")

        for row in reader:
            value = (row.get("wikidata_code") or "").strip()
            if re.fullmatch(r"Q[1-9]\d*", value):
                qids.add(value)

    return sorted(qids)


def get_window(qids, window_number):
    """Return one of 10 contiguous, approximately equal QID windows."""
    start = len(qids) * (window_number - 1) // 10
    end = len(qids) * window_number // 10
    return qids[start:end]


def make_query(qids):
    values = " ".join(f"wd:{qid}" for qid in qids)
    return f"""
    SELECT DISTINCT ?person ?personLabel ?birthDate ?occupationLabel WHERE {{
      VALUES ?person {{ {values} }}

      ?person wdt:P31 wd:Q5;
              wdt:P106 ?occupation;
              p:P569/psv:P569 ?birthValue.

      ?birthValue wikibase:timeValue ?birthDate;
                  wikibase:timePrecision ?precision.
      FILTER(?precision >= 11)

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
        ?person rdfs:label ?personLabel.
        ?occupation rdfs:label ?occupationLabel.
      }}
    }}
    """


def fetch_batch(session, qids):
    query = make_query(qids)

    for attempt in range(6):
        response = session.get(
            ENDPOINT,
            params={"query": query},
            headers=HEADERS,
            timeout=90,
        )

        if response.status_code == 200:
            return response.json()["results"]["bindings"]

        if response.status_code in (429, 503):
            retry_after = response.headers.get("Retry-After")
            try:
                wait = int(retry_after)
            except (TypeError, ValueError):
                try:
                    wait = max(
                        1,
                        int(
                            (
                                parsedate_to_datetime(retry_after)
                                - datetime.now(timezone.utc)
                            ).total_seconds()
                        ),
                    )
                except (TypeError, ValueError):
                    wait = 10 * (attempt + 1)

            time.sleep(wait)
            continue

        response.raise_for_status()

    raise RuntimeError("Wikidata kept throttling requests; try again later.")


def load_output_rows(output_csv):
    if not os.path.exists(output_csv):
        return []

    with open(output_csv, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def write_output(output_csv, rows):
    # Group rows by person and combine their occupations.
    people = {}

    for row in rows:
        qid = row["wikidata_code"]
        person = people.setdefault(
            qid,
            {
                "wikidata_code": qid,
                "name": row["name"],
                "birthdate": row["birthdate"],
                "occupations": set(),
            },
        )

        # Existing output rows may already contain comma-separated occupations.
        occupations = row.get("occupation", "").split(",")
        person["occupations"].update(
            occupation.strip() for occupation in occupations if occupation.strip()
        )

    output_rows = []
    for person in people.values():
        output_rows.append({
            "wikidata_code": person["wikidata_code"],
            "name": person["name"],
            "birthdate": person["birthdate"],
            "occupation": ", ".join(sorted(person["occupations"], key=str.casefold)),
        })

    output_rows.sort(key=lambda row: row["name"].casefold())

    temp_path = output_csv + ".tmp"
    with open(temp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter=";")
        writer.writeheader()
        writer.writerows(output_rows)

    os.replace(temp_path, output_csv)


def main(input_csv, output_csv, window_number):
    all_qids = get_qids(input_csv)
    window_qids = get_window(all_qids, window_number)

    rows = load_output_rows(output_csv)
    written_qids = {
        row["wikidata_code"] for row in rows if row.get("wikidata_code")
    }

    completed_positions = [
        i for i, qid in enumerate(window_qids) if qid in written_qids
    ]
    start = max(completed_positions, default=-1) + 1
    remaining_qids = window_qids[start:]

    print(
        f"Window {window_number}/10: {len(window_qids)} IDs; "
        f"resuming at {start + 1}, {len(remaining_qids)} remaining."
    )

    session = requests.Session()

    for offset in range(0, len(remaining_qids), BATCH_SIZE):
        batch = remaining_qids[offset:offset + BATCH_SIZE]
        bindings = fetch_batch(session, batch)

        for item in bindings:
            rows.append({
                "wikidata_code": item["person"]["value"].rsplit("/", 1)[-1],
                "name": item["personLabel"]["value"],
                "birthdate": item["birthDate"]["value"][:10],
                "occupation": item["occupationLabel"]["value"],
            })

        write_output(output_csv, rows)

        processed = min(start + offset + len(batch), len(window_qids))
        print(f"Processed {processed}/{len(window_qids)} IDs in window {window_number}.")
        time.sleep(PAUSE_SECONDS)

    print(f"Finished window {window_number}; output saved to {output_csv}.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python extract_people.py "
            "input.csv output.csv window_number(1-10)"
        )
        sys.exit(2)

    try:
        window_number = int(sys.argv[3])
        if not 1 <= window_number <= 10:
            raise ValueError
    except ValueError:
        print("window_number must be an integer from 1 to 10.")
        sys.exit(2)

    main(sys.argv[1], sys.argv[2], window_number)
