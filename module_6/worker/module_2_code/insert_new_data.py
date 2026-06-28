"""
Insert new LLM-enriched records into PostgreSQL.

This script inserts only the latest newly pulled and LLM-enriched records
into the PostgreSQL applicants table.

It does not drop or recreate the applicants table. It only inserts new
records and ignores duplicates using ON CONFLICT.
"""

import json
from pathlib import Path

from module_2_code.db_helpers import insert_applicant_records
from shared.db_connection import get_connection


BASE_DIR = Path(__file__).resolve().parent
NEW_LLM_FILE = BASE_DIR / "new_llm_extend_applicant_data.json"


def load_new_records():
    """
    Load the latest newly LLM-enriched records.

    Returns an empty list if the file does not exist.
    """
    if not NEW_LLM_FILE.exists():
        print(f"{NEW_LLM_FILE.name} does not exist. No new records to insert.")
        return []

    with NEW_LLM_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_applicant_count(cursor):
    """Return the current number of applicant rows in PostgreSQL."""
    cursor.execute("SELECT COUNT(*) FROM applicants;")
    return cursor.fetchone()[0]


def main():
    """Insert newly LLM-enriched records into PostgreSQL."""
    print("Loading latest new LLM-enriched records...")

    new_records = load_new_records()
    print(f"New LLM-enriched records found: {len(new_records)}")

    if not new_records:
        print("No new records to insert. Database was not changed.")
        return

    print("Connecting to PostgreSQL...")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            before_count = get_applicant_count(cursor)
            attempted_count = insert_applicant_records(
                cursor,
                new_records,
                count_attempts=True,
            )
            after_count = get_applicant_count(cursor)

    inserted_count = after_count - before_count

    print(f"Attempted to insert: {attempted_count}")
    print(f"Actually inserted: {inserted_count}")
    print(f"Database row count before: {before_count}")
    print(f"Database row count after: {after_count}")


if __name__ == "__main__":
    main()
