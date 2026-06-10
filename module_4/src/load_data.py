import json
import re
from datetime import datetime
from pathlib import Path

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
DATA_FILE = BASE_DIR / "data" / "llm_extend_applicant_data.json"


def clean_float(value):
    """
    Converts messy numeric strings into floats.
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
    Converts date strings into YYYY-MM-DD format.
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
    Converts status strings into a simple admission decision.
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


def create_table(cursor):
    """
    Drops and recreates the applicants table.
    """
    cursor.execute("""
        DROP TABLE IF EXISTS applicants;
    """)

    cursor.execute("""
        CREATE TABLE applicants (
            p_id INTEGER PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa FLOAT,
            gre FLOAT,
            gre_v FLOAT,
            gre_aw FLOAT,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        );
    """)


def load_json_data():
    """
    Loads the JSON applicant records from the data folder.
    """
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def insert_records(cursor, records):
    """
    Inserts applicant records into PostgreSQL.
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
        inserted_count += 1

    return inserted_count


def main():
    print("Connecting to PostgreSQL...")

    connection = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    with connection:
        with connection.cursor() as cursor:
            print("Creating applicants table...")
            create_table(cursor)

            print(f"Loading data from {DATA_FILE}...")
            records = load_json_data()

            print("Inserting records...")
            inserted_count = insert_records(cursor, records)

            print(f"Done. Inserted {inserted_count} records into applicants table.")

            cursor.execute("SELECT COUNT(*) FROM applicants;")
            total_count = cursor.fetchone()[0]
            print(f"Confirmed row count in database: {total_count}")


if __name__ == "__main__":
    main()