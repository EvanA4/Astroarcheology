import csv
import re
import time
from collections import deque
from datetime import date, datetime, time as datetime_time, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, Tag

from zodiac import zodiac_sign

START_URL = "https://en.wikipedia.org/wiki/Lists_of_people_by_occupation"
OUTPUT_FILE = Path(__file__).with_name("data.csv")
REQUEST_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 30
CSV_HEADERS = (
    "FirstName",
    "LastName",
    "Birthday",
    "ClaimedZodiac",
    "Profession",
)
EXCLUDED_CLASSES = {
    "ambox",
    "gallery",
    "hatnote",
    "metadata",
    "navbox",
    "portal",
    "reflist",
    "sidebar",
    "sistersitebox",
    "vertical-navbox",
}


def article_url(url):
    """Return a fragment-free English Wikipedia article URL, or None."""

    parsed = urlsplit(url)
    if parsed.netloc and parsed.netloc.casefold() not in {
        "en.wikipedia.org",
        "www.en.wikipedia.org",
    }:
        return None

    path = parsed.path
    if not path.startswith("/wiki/") or ":" in unquote(path[len("/wiki/") :]):
        return None

    return urlunsplit(("https", "en.wikipedia.org", path, "", ""))


class WikipediaClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "AstroarcheologyWikipediaScraper/1.0 "
                    "(educational research project)"
                )
            }
        )
        self.pages = {}
        self.last_request = 0.0

    def get_page(self, url):
        url = article_url(url)
        if url is None:
            raise ValueError(f"Not an English Wikipedia article URL: {url!r}")
        if url in self.pages:
            return self.pages[url]

        wait = REQUEST_DELAY_SECONDS - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)

        response = self.session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        self.last_request = time.monotonic()
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        canonical_link = soup.select_one('link[rel="canonical"]')
        canonical_url = article_url(
            urljoin(response.url, canonical_link["href"])
            if canonical_link and canonical_link.get("href")
            else response.url
        )

        result = (soup, canonical_url)
        self.pages[url] = result
        if canonical_url is not None:
            self.pages[canonical_url] = result
        return result


def get_article_content(soup):
    """Get the main article content or report a changed page structure."""

    content = soup.select_one("#mw-content-text .mw-parser-output")
    if content is None:
        raise ValueError("Could not find the Wikipedia article content.")
    return content


def get_profession_lists(soup):
    """Return root occupation labels paired with their linked list pages."""

    content = get_article_content(soup)
    root_lists = []
    seen = set()
    wanted_sections = {"Lists of lists", "List of..."}

    for heading in content.select("h2"):
        section_name = heading.get_text(" ", strip=True)
        if section_name == "Notes":
            break
        if section_name not in wanted_sections:
            continue

        for section_part in heading.parent.next_siblings:
            if (
                isinstance(section_part, Tag)
                and section_part.find("h2", recursive=False)
            ):
                break
            if not isinstance(section_part, Tag):
                continue

            for item in section_part.select("li"):
                if item.find_parent("li") is not None:
                    continue
                direct_links = item.find_all("a", href=True, recursive=False)
                if not direct_links:
                    continue

                profession = direct_links[0].get_text(" ", strip=True)
                profession = re.sub(
                    r"^lists?\s+of\s+",
                    "",
                    profession,
                    flags=re.IGNORECASE,
                ).strip()
                if not profession:
                    continue

                for link in item.select("a[href]"):
                    linked_url = article_url(urljoin(START_URL, link["href"]))
                    key = (profession.casefold(), linked_url)
                    if linked_url and key not in seen:
                        root_lists.append((linked_url, profession))
                        seen.add(key)

    if not root_lists:
        raise ValueError("Could not find occupation lists on the Wikipedia page.")
    return root_lists


def has_excluded_ancestor(element, content):
    current = element
    while isinstance(current, Tag) and current is not content:
        if EXCLUDED_CLASSES.intersection(current.get("class", [])):
            return True
        current = current.parent
    return False


def get_list_page_links(soup, page_url):
    """Return article links in the lists and tables of an occupation page."""

    content = get_article_content(soup)
    links = []
    seen = set()

    for item in content.select("li"):
        if has_excluded_ancestor(item, content):
            continue
        for anchor in item.find_all("a", href=True):
            target = article_url(urljoin(page_url, anchor["href"]))
            if target and target != page_url and target not in seen:
                links.append(target)
                seen.add(target)

    for row in content.select("table tr"):
        if has_excluded_ancestor(row, content):
            continue
        for anchor in row.select("th a[href], td a[href]"):
            target = article_url(urljoin(page_url, anchor["href"]))
            if target and target != page_url and target not in seen:
                links.append(target)
                seen.add(target)

    return links


def is_list_page(soup, page_url):
    """Identify list articles so biography pages without birthdays are skipped."""

    title = unquote(urlsplit(page_url).path.rsplit("/", 1)[-1]).replace("_", " ")
    if re.match(r"^lists?\s+of\b", title, flags=re.IGNORECASE):
        return True

    categories = soup.select("#catlinks a")
    return any(
        "list" in category.get_text(" ", strip=True).casefold()
        for category in categories
    )


def get_birthday(soup):
    """Return a full ISO date of birth, ignoring year- or month-only dates."""

    for element in soup.select(".bday"):
        for value in (element.get("datetime"), element.get_text(" ", strip=True)):
            if not value:
                continue
            try:
                return date.fromisoformat(value.strip())
            except ValueError:
                continue
    return None


def get_person(soup, page_url, profession):
    """Build a CSV row for an article with a complete date of birth."""

    birthday = get_birthday(soup)
    if birthday is None:
        return None

    heading = soup.select_one("#firstHeading")
    name = heading.get_text(" ", strip=True) if heading else ""
    name = re.sub(r"\s+\([^()]*\)$", "", name).strip()
    name_parts = name.split()
    if not name_parts:
        return None

    birthday_datetime = datetime.combine(
        birthday,
        datetime_time.min,
        tzinfo=timezone.utc,
    )
    return {
        "FirstName": name_parts[0],
        "LastName": " ".join(name_parts[1:]),
        "Birthday": birthday.isoformat(),
        "ClaimedZodiac": zodiac_sign(birthday_datetime),
        "Profession": profession,
        "_dedupe_key": (page_url, birthday.isoformat()),
        "_name_key": (" ".join(name_parts).casefold(), birthday.isoformat()),
    }


def write_people(people):
    """Write scraped people with the existing CSV column headers."""

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(
            {header: person[header] for header in CSV_HEADERS}
            for person in people
        )
    print(f"Saved {len(people)} people to {OUTPUT_FILE}")


def scrape():
    client = WikipediaClient()
    root_soup, _ = client.get_page(START_URL)
    page_queue = deque(
        (url, profession, True)
        for url, profession in get_profession_lists(root_soup)
    )
    visited_lists = set()
    failed_pages = set()
    failures = []
    seen_people = set()
    people = []

    while page_queue:
        url, profession, is_root_list = page_queue.popleft()
        if url in failed_pages:
            continue
        try:
            soup, canonical_url = client.get_page(url)
        except requests.RequestException as error:
            if url not in failed_pages:
                message = f"Could not load {url}: {error}"
                print(f"ERROR: {message}")
                failures.append(message)
                failed_pages.add(url)
            continue

        if canonical_url is None:
            print(
                f"Skipping {url}: Wikipedia resolves it to a non-article "
                "page."
            )
            continue

        visit_key = (canonical_url, profession.casefold())
        if visit_key in visited_lists:
            continue
        visited_lists.add(visit_key)

        if is_root_list or is_list_page(soup, canonical_url):
            page_links = get_list_page_links(soup, canonical_url)
            page_queue.extend(
                (target, profession, False) for target in page_links
            )
            print(
                f"Scanned list for {profession}: {canonical_url} "
                f"({len(page_links)} linked pages; "
                f"{len(visited_lists)} lists scanned)"
            )
            continue

        person = get_person(soup, canonical_url, profession)
        if person is None:
            continue

        if (
            person["_dedupe_key"] in seen_people
            or person["_name_key"] in seen_people
        ):
            continue
        seen_people.add(person["_dedupe_key"])
        seen_people.add(person["_name_key"])
        del person["_dedupe_key"]
        del person["_name_key"]
        people.append(person)

    write_people(people)
    print(f"Scraped {len(people)} people with complete birthdays.")
    if failures:
        raise RuntimeError(
            f"{len(failures)} Wikipedia pages could not be processed; "
            f"the CSV may be incomplete:\n- " + "\n- ".join(failures)
        )
    if not people:
        raise RuntimeError("No people with complete birthdays were found.")


if __name__ == "__main__":
    scrape()
