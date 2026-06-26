"""Create a small real applicant_data.json subset for Module 6 Docker seed data."""

import json
from pathlib import Path


SOURCE_FILE = Path("src/data/llm_extend_applicant_data.json")
OUTPUT_FILE = Path("data/applicant_data.json")
MAX_RECORDS = 50


def main():
    """Create a small direct subset from the real cleaned dataset."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Could not find source file: {SOURCE_FILE}")

    with SOURCE_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    subset = records[:MAX_RECORDS]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(subset, file, indent=2)

    print(f"Created {OUTPUT_FILE} with {len(subset)} records.")


if __name__ == "__main__":
    main()