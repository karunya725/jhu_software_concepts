"""Load cleaned Grad Cafe applicant seed data into PostgreSQL for Docker."""

import json
import os
from pathlib import Path

from module_2_code.db_helpers import insert_applicant_records
from shared.db_connection import get_connection


DATA_FILE = Path(os.environ.get("SEED_JSON", "/data/applicant_data.json"))


def load_json_data():
    """Load JSON applicant records from the mounted data folder."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_applicant_count(cursor):
    """Return the current number of applicant rows in PostgreSQL."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM applicants;
    """)
    return cursor.fetchone()[0]


def main():  # pragma: no cover
    """Load applicant seed records into the PostgreSQL database."""
    print("Connecting to PostgreSQL...", flush=True)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            print(f"Loading data from {DATA_FILE}...", flush=True)
            records = load_json_data()

            print("Inserting records...", flush=True)
            inserted_count = insert_applicant_records(cursor, records)

            print(
                f"Done. Inserted {inserted_count} records into applicants table.",
                flush=True,
            )

            total_count = get_applicant_count(cursor)
            print(f"Confirmed row count in database: {total_count}", flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()
