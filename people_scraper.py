
import csv
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://bdaydata.com"
PROFESSIONS_FILE = Path(__file__).with_name("professions.csv")
OUTPUT_FILE = Path(__file__).with_name("data.csv")
REQUEST_DELAY_SECONDS = 2


def profession_url(name):
    """Build a profession page URL from a name in the professions CSV."""

    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return urljoin(BASE_URL, f"/profession/{slug}")


def read_profession_names():
    """Read profession names from the generated professions CSV."""

    with PROFESSIONS_FILE.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"{PROFESSIONS_FILE} is empty or has no header.")

        profession_column = next(
            (
                field
                for field in reader.fieldnames
                if field.strip().casefold() == "profession"
            ),
            None,
        )
        if profession_column is None:
            raise ValueError(
                f"{PROFESSIONS_FILE} must have a 'Profession' column."
            )

        profession_names = [
            row[profession_column].strip()
            for row in reader
            if row.get(profession_column) and row[profession_column].strip()
        ]

    if not profession_names:
        raise ValueError(f"No professions were found in {PROFESSIONS_FILE}.")

    return profession_names


def load_all_people(page):
    """Click Load More until all celebrities are displayed."""

    while True:
        button = page.get_by_role(
            "button",
            name=re.compile("Load More Celebrities")
        )

        if button.count() == 0:
            break

        old_count = page.locator('a[href^="/people/"]').count()

        try:
            button.click(timeout=10000)

            page.wait_for_function(
                """oldCount =>
                    document.querySelectorAll(
                        'a[href^="/people/"]'
                    ).length > oldCount
                """,
                arg=old_count,
                timeout=15000
            )
            time.sleep(REQUEST_DELAY_SECONDS)

        except PlaywrightTimeoutError:
            print("  Warning: Load More did not return new results.")
            break

    return BeautifulSoup(page.content(), "html.parser")


def get_people(soup, profession):
    """Extract celebrity names and profile URLs."""

    people = {}

    for link in soup.select('a[href^="/people/"]'):
        heading = link.select_one("h3")

        if not heading:
            continue

        name = heading.get_text(" ", strip=True)
        url = urljoin(BASE_URL, link["href"])

        if name:
            people[url] = {
                "profession": profession,
                "name": name,
                "url": url
            }

    return list(people.values())


def format_birthday_utc(value):
    """Convert a birthday to an ISO 8601 UTC timestamp."""

    value = value.strip()
    if not value:
        return ""

    birthday = None
    for date_format in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            birthday = datetime.strptime(value, date_format)
            break
        except ValueError:
            continue

    if birthday is None:
        try:
            birthday = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return ""

    if birthday.tzinfo is None:
        birthday = birthday.replace(tzinfo=timezone.utc)
    else:
        birthday = birthday.astimezone(timezone.utc)

    return birthday.isoformat(timespec="seconds").replace("+00:00", "Z")


def get_profile_data(soup, fallback_name, fallback_profession):
    """Extract the requested details from a person's profile page."""

    facts = {}
    for row in soup.select("table tr"):
        label = row.find("th")
        value = row.find("td")
        if label and value:
            facts[label.get_text(" ", strip=True).casefold()] = (
                value.get_text(" ", strip=True)
            )

    name = facts.get("full name") or fallback_name
    name_parts = name.split()

    return {
        "FirstName": name_parts[0] if name_parts else "",
        "LastName": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
        "Birthday": format_birthday_utc(facts.get("birthday", "")),
        "ClaimedZodiac": facts.get("zodiac sign", ""),
        "Profession": facts.get("profession") or fallback_profession,
    }


def write_people(people):
    """Save all scraped people to the output CSV file."""

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "FirstName",
                "LastName",
                "Birthday",
                "ClaimedZodiac",
                "Profession",
            ],
        )
        writer.writeheader()
        writer.writerows(people)

    print(f"Saved: {OUTPUT_FILE}")


def scrape():
    requested_professions = read_profession_names()
    failures = []
    all_people = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                )
            )

            for profession in requested_professions:
                url = profession_url(profession)
                print(f"\nFinding people listed as {profession}...")

                try:
                    response = page.goto(url, wait_until="domcontentloaded")
                    if response and response.status >= 400:
                        raise RuntimeError(f"HTTP {response.status}")
                    page.locator("h1").wait_for(timeout=15000)
                    people = get_people(load_all_people(page), profession)
                except Exception as error:
                    message = (
                        f"Could not load profession {profession!r}: {error}"
                    )
                    print(f"ERROR: {message}")
                    failures.append(message)
                    continue

                print(
                    f"Found {len(people)} people. "
                    "Fetching profile details...\n"
                )

                for index, person in enumerate(people, 1):
                    print(f"[{index}/{len(people)}] {person['name']}")

                    try:
                        page.goto(person["url"], wait_until="domcontentloaded")
                        page.locator("h1").wait_for(timeout=15000)
                        profile = get_profile_data(
                            BeautifulSoup(page.content(), "html.parser"),
                            person["name"],
                            profession,
                        )
                        if not profile["Birthday"]:
                            print(
                                "  WARNING: Birthday was missing or not "
                                "recognized."
                            )
                        all_people.append(profile)
                    except Exception as error:
                        print(f"  ERROR: Could not scrape profile: {error}")
                        all_people.append(
                            get_profile_data(
                                BeautifulSoup("", "html.parser"),
                                person["name"],
                                profession,
                            )
                        )

                    time.sleep(REQUEST_DELAY_SECONDS)

                print(f"Profession: {profession}")
                print(f"People processed: {len(people)}")
                time.sleep(REQUEST_DELAY_SECONDS)
        finally:
            browser.close()

    write_people(all_people)
    print("\n========== FINISHED ==========")
    if failures:
        raise RuntimeError(
            "Some professions could not be processed:\n- "
            + "\n- ".join(failures)
        )


if __name__ == "__main__":
    scrape()
