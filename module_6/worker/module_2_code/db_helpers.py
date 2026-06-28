"""Shared PostgreSQL helpers for Grad Cafe applicant inserts."""

import re
from datetime import datetime


INSERT_APPLICANT_SQL = """
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

    cleaned_value = str(value).strip()

    if cleaned_value == "":
        return None

    match = re.search(r"\d+(\.\d+)?", cleaned_value)

    if match:
        return float(match.group())

    return None


def clean_date(value):
    """
    Convert date strings into YYYY-MM-DD date objects.

    Example:
        "Added on May 29, 2026" -> date(2026, 5, 29)
    """
    if value is None:
        return None

    cleaned_value = str(value).replace("Added on", "").strip()

    try:
        parsed_date = datetime.strptime(cleaned_value, "%B %d, %Y")
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

    cleaned_value = str(value).strip()

    if "Accepted" in cleaned_value:
        return "Accepted"
    if "Rejected" in cleaned_value:
        return "Rejected"
    if "Wait" in cleaned_value:
        return "Wait listed"
    if "Interview" in cleaned_value:
        return "Interview"

    return cleaned_value


def build_applicant_row(record):
    """Build one PostgreSQL applicant row tuple from a cleaned applicant record."""
    raw_record = record.get("raw_record", {})
    p_id = record.get("gradcafe_id") or raw_record.get("id")

    if p_id is None:
        return None

    return (
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


def insert_applicant_records(cursor, records, count_attempts=False):
    """
    Insert applicant records into PostgreSQL.

    Duplicate p_id values are ignored by the database.

    When count_attempts is False, the function returns the number of rows
    actually inserted according to cursor.rowcount.

    When count_attempts is True, the function returns the number of valid
    insert attempts. This is useful when the caller separately compares row
    counts before and after insertion.
    """
    insert_count = 0

    for record in records:
        row = build_applicant_row(record)

        if row is None:
            print("Skipping one record because it has no Grad Cafe ID.")
            continue

        cursor.execute(INSERT_APPLICANT_SQL, row)

        if count_attempts:
            insert_count += 1
        else:
            insert_count += cursor.rowcount

    return insert_count
