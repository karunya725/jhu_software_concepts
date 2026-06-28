"""Shared JSON file helpers for Module 6 pipeline files."""

import json
from pathlib import Path


def load_json_file(filename, default=None):
    """Load JSON data from a file, returning a default value if missing."""
    input_path = Path(filename)

    if not input_path.exists():
        if default is not None:
            return default
        return []

    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json_file(data, filename):
    """Save data to a JSON file."""
    output_path = Path(filename)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(data)} records to {output_path}")
