"""Load cleaned Grad Cafe applicant seed data into PostgreSQL for Docker."""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import psycopg


DATABASE_URL = os.environ["DATABASE_URL"]
DATA_FILE = Path(os.environ.get("SEED_JSON", "/data/applicant_data.json"))


def get_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg.connect(DATABASE_URL)


def clean_float(value):
    """
    Convert messy numeric strings into floats.

    Examples:
        "GPA 3.90" -> 3.90
        "165" -> 165.0
        None -> None
    """
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    match = re.search(r"\d+(\.\d+)?", value)
    if match:
        return float(match.group())

    return None


def clean_date(value):
    """
    Convert date strings into YYYY-MM-DD format.

    Example:
        "Added on May 29, 2026" -> "2026-05-29"
    """
    if value is None:
        return None

    value = str(value).replace("Added on", "").strip()

    try:
        parsed_date = datetime.strptime(value, "%B %d, %Y")
        return parsed_date.date()
    except ValueError:
        return None


def clean_status(value):
    """
    Convert status strings into a simple admission decision.

    Examples:
        "Accepted on May 29" -> "Accepted"
        "Rejected on May 29" -> "Rejected"
        "Wait listed" -> "Wait listed"
    """
    if value is None:
        return None

    value = str(value).strip()

    if "Accepted" in value:
        return "Accepted"
    if "Rejected" in value:
        return "Rejected"
    if "Wait" in value:
        return "Wait listed"
    if "Interview" in value:
        return "Interview"

    return value


def load_json_data():
    """Load JSON applicant records from the mounted data folder."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def insert_records(cursor, records):
    """Insert applicant records into PostgreSQL using parameterized values."""
    insert_sql = """
        INSERT INTO applicants (
            p_id,
            program,
            comments,
            date_added,
            url,
            status,
            term,
            us_or_international,
            gpa,
            gre,
            gre_v,
            gre_aw,
            degree,
            llm_generated_program,
            llm_generated_university
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (p_id) DO NOTHING;
    """

    inserted_count = 0

    for record in records:
        raw_record = record.get("raw_record", {})
        p_id = record.get("gradcafe_id") or raw_record.get("id")

        if p_id is None:
            continue

        row = (
            int(p_id),
            record.get("program"),
            record.get("comments"),
            clean_date(record.get("date_added")),
            record.get("url"),
            clean_status(record.get("status")),
            record.get("term"),
            record.get("US/International"),
            clean_float(record.get("GPA")),
            clean_float(raw_record.get("greq")),
            clean_float(raw_record.get("grev")),
            clean_float(raw_record.get("grew")),
            record.get("Degree"),
            record.get("llm-generated-program"),
            record.get("llm-generated-university"),
        )

        cursor.execute(insert_sql, row)
        inserted_count += cursor.rowcount

    return inserted_count


def main():  # pragma: no cover
    """Load applicant records into the PostgreSQL database."""
    print("Connecting to PostgreSQL...", flush=True)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            print(f"Loading data from {DATA_FILE}...", flush=True)
            records = load_json_data()

            print("Inserting records...", flush=True)
            inserted_count = insert_records(cursor, records)

            print(
                f"Done. Inserted {inserted_count} records into applicants table.",
                flush=True,
            )

            cursor.execute("""
                SELECT COUNT(*)
                FROM applicants;
            """)
            total_count = cursor.fetchone()[0]
            print(f"Confirmed row count in database: {total_count}", flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()