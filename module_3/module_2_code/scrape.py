"""
Module 2 / Module 3 - Grad Cafe Scraper

This file handles scraping only:
- Builds Grad Cafe URLs using urllib
- Requests public Grad Cafe survey pages
- Extracts raw applicant records from the embedded page JSON
- Saves raw applicant records to raw_applicant_data.json

For Module 3 Part B:
- It checks recent Grad Cafe pages for new records
- Saves only newly found records to new_raw_applicant_data.json
- Appends those new records to raw_applicant_data.json
- Avoids duplicates using Grad Cafe record IDs

Data cleaning is handled separately in clean.py / clean_new_data.py.
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
NEW_RAW_OUTPUT_FILE = "new_raw_applicant_data.json"


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
            "User-Agent": "Mozilla/5.0 (compatible; student data collection script; educational use)"
        },
    )

    try:
        with urlopen(request, timeout=45) as response:
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


def fetch_page_with_retries(url, max_retries=3, delay_seconds=10):
    """
    Fetch a page with limited polite retries.
    """
    for attempt_number in range(1, max_retries + 1):
        print(f"Request attempt {attempt_number} of {max_retries}")

        page_html = fetch_page(url)

        if page_html is not None:
            return page_html

        if attempt_number < max_retries:
            print(f"Request failed. Waiting {delay_seconds} seconds before retrying...")
            time.sleep(delay_seconds)

    print("All retry attempts failed. Stopping scrape.")
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


def load_data(filename):
    """
    Load JSON data from a file.
    Returns an empty list if the file does not exist yet.
    """
    input_path = Path(filename)

    if not input_path.exists():
        print(f"{filename} does not exist yet. Starting with an empty list.")
        return []

    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data, filename):
    """
    Save records as JSON.
    """
    output_path = Path(filename)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(data)} records to {output_path}")


def _get_seen_ids(records):
    """
    Build a set of existing Grad Cafe record IDs.
    """
    seen_ids = set()

    for record in records:
        record_id = record.get("id")

        if record_id is not None:
            seen_ids.add(record_id)

    return seen_ids


def scrape_data(start_page=1, max_pages=1550, target_records=30000):
    """
    Full scrape mode.

    It loads existing raw records, avoids duplicates, and saves to raw_applicant_data.json.
    """
    all_raw_records = load_data(RAW_OUTPUT_FILE)
    seen_ids = _get_seen_ids(all_raw_records)

    for page_number in range(start_page, max_pages + 1):
        print(f"\nScraping page {page_number} of {max_pages}...")

        url = build_gradcafe_url(page=page_number, program="Computer Science")

        time.sleep(3)

        page_html = fetch_page_with_retries(url)

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

        new_records = []

        for record in raw_records:
            record_id = record.get("id")

            if record_id is not None and record_id not in seen_ids:
                new_records.append(record)
                seen_ids.add(record_id)

        print(f"Found {len(raw_records)} raw applicant records on page {page_number}.")
        print(f"New records added from this page: {len(new_records)}")

        all_raw_records.extend(new_records)

        save_data(all_raw_records, RAW_OUTPUT_FILE)
        print(f"Progress saved. Total raw records so far: {len(all_raw_records)}")

        if len(all_raw_records) >= target_records:
            print(f"Reached at least {target_records} records. Stopping scrape.")
            break

    print(f"\nFinal raw records collected: {len(all_raw_records)}")

    return all_raw_records


def scrape_new_data(
    start_page=1,
    max_pages=10,
    stop_after_empty_pages=2,
    program="Computer Science"
):
    """
    Incremental scrape mode

    This function:
    1. Loads the existing full raw dataset from raw_applicant_data.json.
    2. Scrapes recent Grad Cafe pages, starting from page 1.
    3. Saves only newly found records to new_raw_applicant_data.json.
    4. Appends newly found records to raw_applicant_data.json.
    5. Stops early after repeated pages with no new records.

    This is intended for the Flask Pull Data button.
    """
    all_raw_records = load_data(RAW_OUTPUT_FILE)
    seen_ids = _get_seen_ids(all_raw_records)

    all_new_records = []
    consecutive_empty_pages = 0

    print("\nStarting incremental scrape for new Grad Cafe data...")
    print(f"Existing raw records: {len(all_raw_records)}")
    print(f"Checking pages {start_page} to {max_pages}")
    print(f"Program filter: {program}")

    for page_number in range(start_page, max_pages + 1):
        print(f"\nChecking recent page {page_number} of {max_pages}...")

        url = build_gradcafe_url(page=page_number, program=program)

        time.sleep(3)

        page_html = fetch_page_with_retries(url)

        if page_html is None:
            print("No HTML was collected. Stopping incremental scrape.")
            break

        page_json = _extract_page_json(page_html)

        if page_json is None:
            print("No page JSON was extracted. Stopping incremental scrape.")
            break

        raw_records = _extract_raw_records(page_json)

        if not raw_records:
            print("No raw records found. Stopping incremental scrape.")
            break

        new_records_this_page = []

        for record in raw_records:
            record_id = record.get("id")

            if record_id is not None and record_id not in seen_ids:
                new_records_this_page.append(record)
                seen_ids.add(record_id)

        print(f"Found {len(raw_records)} records on page {page_number}.")
        print(f"New records found on this page: {len(new_records_this_page)}")

        if new_records_this_page:
            all_new_records.extend(new_records_this_page)
            consecutive_empty_pages = 0
        else:
            consecutive_empty_pages += 1
            print(f"No new records on this page. Empty page streak: {consecutive_empty_pages}")

        if consecutive_empty_pages >= stop_after_empty_pages:
            print(
                f"Found {stop_after_empty_pages} consecutive pages with no new records. "
                "Stopping incremental scrape."
            )
            break

    # Save the new-only raw file every time.
    # If there are no new records, this file will contain [].
    save_data(all_new_records, NEW_RAW_OUTPUT_FILE)

    if all_new_records:
        print(f"\nAppending {len(all_new_records)} new records to {RAW_OUTPUT_FILE}...")
        all_raw_records.extend(all_new_records)
        save_data(all_raw_records, RAW_OUTPUT_FILE)
    else:
        print("\nNo new records found. Existing raw file was not changed.")

    print("\nIncremental scrape complete.")
    print(f"Total new records found: {len(all_new_records)}")
    print(f"Total raw records now: {len(all_raw_records)}")

    return all_new_records


if __name__ == "__main__":
    # Default behavior for Module 3 Part B:
    # check for new records only.
    scrape_new_data(
        start_page=1,
        max_pages=10,
        stop_after_empty_pages=2,
        program="Computer Science"
    )