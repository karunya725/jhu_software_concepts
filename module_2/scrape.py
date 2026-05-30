"""
Module 2 - Grad Cafe Scraper

This file handles scraping only:
- Builds Grad Cafe URLs using urllib
- Requests public Grad Cafe survey pages
- Extracts raw applicant records from the embedded page JSON
- Saves raw applicant records to raw_applicant_data.json

Data cleaning is handled separately in clean.py.
"""

from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import html
import json
import time


BASE_URL = "https://www.thegradcafe.com/"
SURVEY_PATH = "survey/"
RAW_OUTPUT_FILE = "raw_applicant_data.json"


def build_gradcafe_url(page=1, program=None):
    """
    Build a Grad Cafe survey URL using urllib tools.
    """
    survey_url = urljoin(BASE_URL, SURVEY_PATH)

    query_params = {}

    if page is not None:
        query_params["page"] = page

    if program:
        query_params["program"] = program

    query_string = urlencode(query_params)

    if query_string:
        return f"{survey_url}?{query_string}"

    return survey_url


def fetch_page(url):
    """
    Fetch one Grad Cafe page using urllib.

    Returns page HTML if successful. Returns None if the request fails,
    is blocked, or is rate-limited.
    """
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; JHU student scraper; educational use)"
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            status_code = response.status
            content_type = response.headers.get("Content-Type", "")

            print(f"URL: {url}")
            print(f"Status code: {status_code}")
            print(f"Content-Type: {content_type}")

            if status_code != 200:
                print("Request was not successful. Stopping.")
                return None

            html_bytes = response.read()
            return html_bytes.decode("utf-8", errors="replace")

    except HTTPError as error:
        print(f"HTTP error: {error.code}")

        if error.code in [403, 429, 503]:
            print("The site blocked, rate-limited, or rejected the request. Stopping.")

        return None

    except URLError as error:
        print(f"URL error: {error.reason}")
        return None

    except TimeoutError:
        print("Request timed out.")
        return None


def _extract_page_json(page_html):
    """
    Extract JSON from the page's data-page attribute.
    """
    soup = BeautifulSoup(page_html, "html.parser")

    app_div = soup.find("div", id="app")

    if app_div is None:
        print("Could not find div with id='app'.")
        return None

    data_page = app_div.get("data-page")

    if not data_page:
        print("Could not find data-page attribute.")
        return None

    decoded_data_page = html.unescape(data_page)

    try:
        return json.loads(decoded_data_page)
    except json.JSONDecodeError as error:
        print(f"Could not decode data-page JSON: {error}")
        return None


def _extract_raw_records(page_json):
    """
    Extract the raw applicant records from the page JSON.
    """
    return (
        page_json
        .get("props", {})
        .get("results", {})
        .get("data", [])
    )


def save_data(data, filename=RAW_OUTPUT_FILE):
    """
    Save raw applicant records as JSON.
    """
    output_path = Path(filename)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(data)} raw records to {output_path}")


def load_data(filename=RAW_OUTPUT_FILE):
    """
    Load raw applicant records from JSON.
    """
    input_path = Path(filename)

    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def scrape_data(max_pages=50):
    """
    Pull multiple test pages from Grad Cafe and save raw applicant records.

    This version starts small: 5 pages should give about 100 records.
    """
    all_raw_records = []

    for page_number in range(1, max_pages + 1):
        print(f"\nScraping page {page_number} of {max_pages}...")

        url = build_gradcafe_url(page=page_number, program="Computer Science")

        # Polite delay before each request.
        time.sleep(2)

        page_html = fetch_page(url)

        if page_html is None:
            print("No HTML was collected. Stopping scrape.")
            break

        page_json = _extract_page_json(page_html)

        if page_json is None:
            print("No page JSON was extracted. Stopping scrape.")
            break

        raw_records = _extract_raw_records(page_json)

        if not raw_records:
            print("No raw records found. Stopping scrape.")
            break

        print(f"Found {len(raw_records)} raw applicant records on page {page_number}.")

        all_raw_records.extend(raw_records)

    save_data(all_raw_records, RAW_OUTPUT_FILE)

    print(f"\nTotal raw records collected: {len(all_raw_records)}")

    return all_raw_records


if __name__ == "__main__":
    scrape_data()