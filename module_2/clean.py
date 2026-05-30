"""
Module 2 - Data Cleaning

This file converts raw Grad Cafe applicant records into structured applicant dictionaries.
"""

from pathlib import Path
from urllib.parse import urljoin
import json


BASE_URL = "https://www.thegradcafe.com/"
RAW_OUTPUT_FILE = "raw_applicant_data.json"
CLEAN_OUTPUT_FILE = "applicant_data.json"


def _build_entry_url(applicant_id):
    """
    Build the public Grad Cafe result URL for a specific applicant entry.
    """
    if applicant_id is None:
        return None

    return urljoin(BASE_URL, f"result/{applicant_id}")


def _make_raw_text(raw_record):
    """
    Preserve a raw traceability string from the original Grad Cafe record.

    This helps satisfy the assignment requirement to preserve original raw
    applicant listing text for traceability and reproducibility.
    """
    raw_parts = [
        f"School: {raw_record.get('school')}",
        f"Program: {raw_record.get('program')}",
        f"Level: {raw_record.get('level')}",
        f"Decision: {raw_record.get('decision')}",
        f"Decision label: {raw_record.get('decision_label')}",
        f"Added on: {raw_record.get('added_on_label')}",
        f"Season: {raw_record.get('season')}",
        f"Status: {raw_record.get('status')}",
        f"GPA: {raw_record.get('ugpa')}",
        f"GRE Quant: {raw_record.get('greq')}",
        f"GRE Verbal: {raw_record.get('grev')}",
        f"GRE AW: {raw_record.get('grew')}",
        f"GRE Subject: {raw_record.get('gres')}",
        f"Notes: {raw_record.get('notes')}",
    ]

    return " | ".join(str(part) for part in raw_parts)


def _parse_entry(raw_record):
    """
    Convert one raw Grad Cafe applicant record into the assignment's
    required JSON structure.
    """
    applicant_id = raw_record.get("id")

    return {
        "program_name": raw_record.get("program"),
        "university": raw_record.get("school"),
        "comments": raw_record.get("notes"),
        "date_added": raw_record.get("created_at"),
        "entry_url": _build_entry_url(applicant_id),
        "applicant_status": raw_record.get("decision"),
        "acceptance_date": raw_record.get("acceptedDate"),
        "rejection_date": raw_record.get("rejectedDate"),
        "program_start": raw_record.get("season"),
        "student_type": raw_record.get("status"),
        "gre_score": raw_record.get("greq"),
        "gre_v_score": raw_record.get("grev"),
        "degree_type": raw_record.get("level"),
        "gpa": raw_record.get("ugpa"),
        "gre_aw": raw_record.get("grew"),
        "gradcafe_id": applicant_id,
        "raw_text": _make_raw_text(raw_record),
        "raw_record": raw_record,
    }


def clean_data(raw_records):
    """
    Convert raw Grad Cafe records into structured applicant dictionaries.
    """
    cleaned_records = []

    for raw_record in raw_records:
        try:
            cleaned_records.append(_parse_entry(raw_record))
        except Exception as error:
            print(f"Skipping one record due to parsing error: {error}")

    return cleaned_records


def save_data(data, filename=CLEAN_OUTPUT_FILE):
    """
    Save data as valid JSON.
    """
    output_path = Path(filename)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(data)} records to {output_path}")


def load_data(filename=RAW_OUTPUT_FILE):
    """
    Load JSON data from a file.
    """
    input_path = Path(filename)

    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)
    
def check_duplicate_ids(records, id_key, label):
    """
    Check whether records contain duplicate IDs.
    """
    ids = []

    for record in records:
        ids.append(record.get(id_key))

    total_records = len(ids)
    unique_ids = len(set(ids))
    duplicate_count = total_records - unique_ids

    print(f"{label} total records: {total_records}")
    print(f"{label} unique IDs: {unique_ids}")
    print(f"{label} duplicate records: {duplicate_count}")

    if duplicate_count > 0:
        print(f"Warning: duplicate IDs were found in {label}.")


if __name__ == "__main__":
    raw_data = load_data(RAW_OUTPUT_FILE)
    print(f"Loaded {len(raw_data)} raw records from {RAW_OUTPUT_FILE}")

    check_duplicate_ids(raw_data, "id", "Raw data")

    cleaned_data = clean_data(raw_data)
    save_data(cleaned_data, CLEAN_OUTPUT_FILE)

    print(f"Final cleaned record count: {len(cleaned_data)}")
    check_duplicate_ids(cleaned_data, "gradcafe_id", "Cleaned data")