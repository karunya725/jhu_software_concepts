"""
Run LLM Enrichment on New Data Only

This script runs the copied Module 2 LLM cleaner only on newly cleaned records.

Input:
    new_applicant_data.json

Intermediate output:
    new_llm_extend_applicant_data.jsonl

Final output:
    new_llm_extend_applicant_data.json

The original LLM app command is:
    python app.py --file cleaned_applicant_data.json --stdout > full_out.jsonl
"""

from pathlib import Path
import json
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
LLM_DIR = BASE_DIR / "llm_hosting"

NEW_CLEAN_FILE = BASE_DIR / "new_applicant_data.json"
NEW_LLM_JSONL_FILE = BASE_DIR / "new_llm_extend_applicant_data.jsonl"
NEW_LLM_JSON_FILE = BASE_DIR / "new_llm_extend_applicant_data.json"

LLM_APP_FILE = LLM_DIR / "app.py"


def load_json_list(path):
    if not path.exists():
        print(f"{path.name} does not exist. Using empty list.")
        return []

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json_list(path, records):
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(records)} records to {path}")


def convert_jsonl_to_json(jsonl_path, json_path):
    """
    Convert JSONL output from the LLM app into a normal JSON list.
    """
    records = []

    if not jsonl_path.exists():
        print(f"{jsonl_path.name} does not exist. Saving empty JSON list.")
        save_json_list(json_path, records)
        return records

    with jsonl_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            # Skip non-JSON log lines, just in case the LLM app prints messages.
            if not line.startswith("{"):
                print(f"Skipping non-JSON line {line_number}: {line[:80]}")
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                print(f"Skipping invalid JSON on line {line_number}: {error}")

    save_json_list(json_path, records)
    return records


def run_llm_app():
    """
    Run:
        python app.py --file new_applicant_data.json --stdout > new_llm_extend_applicant_data.jsonl
    """
    if not LLM_APP_FILE.exists():
        raise FileNotFoundError(f"Could not find LLM app at {LLM_APP_FILE}")

    command = [
        sys.executable,
        str(LLM_APP_FILE),
        "--file",
        str(NEW_CLEAN_FILE),
        "--stdout"
    ]

    print("Running LLM enrichment on new cleaned records...")
    print("Command:", " ".join(command))

    with NEW_LLM_JSONL_FILE.open("w", encoding="utf-8") as output_file:
        subprocess.run(
            command,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            check=True,
            cwd=LLM_DIR
        )

    print(f"Saved LLM JSONL output to {NEW_LLM_JSONL_FILE}")


def main():
    print("Preparing to run LLM on newly cleaned data...")

    new_clean_records = load_json_list(NEW_CLEAN_FILE)
    print(f"New cleaned records found: {len(new_clean_records)}")

    if len(new_clean_records) == 0:
        print("No new cleaned records. Skipping LLM enrichment.")
        save_json_list(NEW_LLM_JSON_FILE, [])
        return

    run_llm_app()

    converted_records = convert_jsonl_to_json(
        NEW_LLM_JSONL_FILE,
        NEW_LLM_JSON_FILE
    )

    print(f"LLM enrichment complete. Converted records: {len(converted_records)}")


if __name__ == "__main__":
    main()