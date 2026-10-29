import csv

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

START_URL = "https://en.wikipedia.org/wiki/Lists_of_people_by_occupation"
OUTPUT_FILE = "wikiprofessions.csv"


def get_professions(page):
    """Return the profession names listed on the professions page."""

    page.goto(START_URL, wait_until="domcontentloaded")
    page.locator('a[href^="/profession/"]').first.wait_for()

    soup = BeautifulSoup(page.content(), "html.parser")
    professions = []
    seen = set()

    for link in soup.select('a[href^="/profession/"]'):
        heading = link.select_one("h3")
        if not heading:
            continue

        name = heading.get_text(" ", strip=True)
        if name and name not in seen:
            professions.append(name)
            seen.add(name)

    return professions


def scrape():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            professions = get_professions(page)
        finally:
            browser.close()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as output:
        writer = csv.writer(output)
        writer.writerow(["Profession"])
        writer.writerows([name] for name in professions)

    print(f"Found {len(professions)} professions.")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape()