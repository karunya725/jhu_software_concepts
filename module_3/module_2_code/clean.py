"""
Module 2 - Data Cleaning

This file converts raw Grad Cafe applicant records into cleaned applicant dictionaries
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
        return ""

    return urljoin(BASE_URL, f"result/{applicant_id}")


def _make_raw_text(raw_record):
    """
    Preserve a raw traceability string from the original Grad Cafe record.
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


def _calculate_total_gre_score(gre_qr_score, gre_vr_score):
    """
    Calculate total GRE score as Quantitative Reasoning + Verbal Reasoning.

    Returns None if either score is missing or cannot be converted to an integer.
    """
    if gre_qr_score is None or gre_vr_score is None:
        return None

    try:
        return int(gre_qr_score) + int(gre_vr_score)
    except (ValueError, TypeError):
        return None


def _format_program_field(raw_record):
    """
    Combining program and university.
    """
    program_name = raw_record.get("program") or ""
    university = raw_record.get("school") or ""

    if program_name and university:
        return f"{program_name}, {university}"

    return program_name or university


def _format_date_added(raw_record):
    """
    Formatting date
    Eg: "Added on March 31, 2024"
    """
    added_on_label = raw_record.get("added_on_label")

    if added_on_label:
        return f"Added on {added_on_label}"

    created_at = raw_record.get("created_at")
    
    return created_at or ""


def _format_gpa(raw_record):
    """
    Matching GPA field.
    Eg: "GPA 3.88"
    """
    gpa = raw_record.get("ugpa")

    if gpa:
        return f"GPA {gpa}"

    return ""


def _parse_entry(raw_record):
    """
    Convert one raw Grad Cafe applicant record into cleaned JSON structure.
    """
    applicant_id = raw_record.get("id")

    gre_qr_score = raw_record.get("greq")
    gre_vr_score = raw_record.get("grev")
    gre_aw_score = raw_record.get("grew")
    gre_score = _calculate_total_gre_score(gre_qr_score, gre_vr_score)

    return {
        "program": _format_program_field(raw_record),
        "comments": raw_record.get("notes") or "",
        "date_added": _format_date_added(raw_record),
        "url": _build_entry_url(applicant_id),
        "status": raw_record.get("decision_label") or raw_record.get("decision") or "",
        "term": raw_record.get("season") or "",
        "US/International": raw_record.get("status") or "",
        "GRE Score": gre_score,
        "GRE AW": gre_aw_score,
        "GPA": _format_gpa(raw_record),
        "Degree": raw_record.get("level") or "",
        "gradcafe_id": applicant_id,
        "raw_text": _make_raw_text(raw_record),
        "raw_record": raw_record,
    }


def clean_data(raw_records):
    """
    Convert raw Grad Cafe records into cleaned applicant dictionaries.
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


def print_data_quality_summary(cleaned_records):
    """
    Print a simple missing-value summary for the cleaned fields.
    """
    required_fields = [
        "program",
        "comments",
        "date_added",
        "url",
        "status",
        "term",
        "US/International",
        "GRE Score",
        "GRE AW",
        "GPA",
        "Degree",
        "gradcafe_id",
        "raw_text",
        "raw_record",
    ]

    total_records = len(cleaned_records)

    print("\nData quality summary:")
    print(f"Total cleaned records checked: {total_records}")

    for field in required_fields:
        missing_count = 0

        for record in cleaned_records:
            value = record.get(field)

            if value is None or value == "":
                missing_count += 1

        present_count = total_records - missing_count

        print(f"{field}: {present_count} present, {missing_count} missing")


if __name__ == "__main__":
    raw_data = load_data(RAW_OUTPUT_FILE)
    print(f"Loaded {len(raw_data)} raw records from {RAW_OUTPUT_FILE}")

    check_duplicate_ids(raw_data, "id", "Raw data")

    cleaned_data = clean_data(raw_data)
    save_data(cleaned_data, CLEAN_OUTPUT_FILE)

    print(f"Final cleaned record count: {len(cleaned_data)}")
    check_duplicate_ids(cleaned_data, "gradcafe_id", "Cleaned data")
    print_data_quality_summary(cleaned_data)