"""
Insert New LLM-Enriched Records into PostgreSQL

This script inserts only the latest newly pulled and LLM-enriched records
into the PostgreSQL applicants table.

Input:
    module_2_code/new_llm_extend_applicant_data.json

Database:
    gradcafe_db.applicants

Important:
    This script does not drop or recreate the applicants table.
    It only inserts new records and ignores duplicates using ON CONFLICT.
"""

from pathlib import Path
from datetime import datetime
import json
import re

import psycopg


# -----------------------------
# Database connection settings
# -----------------------------
DB_NAME = "gradcafe_db"
DB_USER = "postgres"
DB_PASSWORD = "jscm3@56psg" 
DB_HOST = "localhost"
DB_PORT = "5432"


# -----------------------------
# File path
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
NEW_LLM_FILE = BASE_DIR / "new_llm_extend_applicant_data.json"


def clean_float(value):
    """
    Converts messy numeric strings into floats.

    Examples:
        "GPA 3.90" -> 3.90
        "163" -> 163.0
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
    Converts date strings into YYYY-MM-DD format.

    Example:
        "Added on May 29, 2026" -> date(2026, 5, 29)
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
    Converts status strings into a simple admission decision.

    Examples:
        "Accepted on May 29" -> "Accepted"
        "Rejected on May 29" -> "Rejected"
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


def load_new_records():
    """
    Loads the latest newly LLM-enriched records.
    Returns an empty list if the file does not exist.
    """
    if not NEW_LLM_FILE.exists():
        print(f"{NEW_LLM_FILE.name} does not exist. No new records to insert.")
        return []

    with NEW_LLM_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_connection():
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def insert_records(cursor, records):
    """
    Inserts new applicant records into PostgreSQL.

    Duplicate p_id values are ignored.
    """
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

    attempted_count = 0

    for record in records:
        raw_record = record.get("raw_record", {})

        p_id = record.get("gradcafe_id") or raw_record.get("id")

        if p_id is None:
            print("Skipping one record because it has no Grad Cafe ID.")
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
            clean_float(raw_record.get("greq")),   # GRE Quant
            clean_float(raw_record.get("grev")),   # GRE Verbal
            clean_float(raw_record.get("grew")),   # GRE Analytical Writing
            record.get("Degree"),
            record.get("llm-generated-program"),
            record.get("llm-generated-university"),
        )

        cursor.execute(insert_sql, row)
        attempted_count += 1

    return attempted_count


def main():
    print("Loading latest new LLM-enriched records...")

    new_records = load_new_records()
    print(f"New LLM-enriched records found: {len(new_records)}")

    if len(new_records) == 0:
        print("No new records to insert. Database was not changed.")
        return

    print("Connecting to PostgreSQL...")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM applicants;")
            before_count = cursor.fetchone()[0]

            attempted_count = insert_records(cursor, new_records)

            cursor.execute("SELECT COUNT(*) FROM applicants;")
            after_count = cursor.fetchone()[0]

    inserted_count = after_count - before_count

    print(f"Attempted to insert: {attempted_count}")
    print(f"Actually inserted: {inserted_count}")
    print(f"Database row count before: {before_count}")
    print(f"Database row count after: {after_count}")


if __name__ == "__main__":
    main()