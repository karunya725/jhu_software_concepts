"""
Pull New Data Pipeline

This script is the single command Flask will call when the user clicks
the "Pull Data" button.

New robust pipeline:
1. scrape.py
   - checks recent Grad Café pages
   - saves only new raw records to new_raw_applicant_data.json
   - appends new raw records into raw_applicant_data.json

2. clean_new_data.py
   - cleans only new_raw_applicant_data.json
   - saves new_applicant_data.json

3. run_llm_on_new_data.py
   - runs LLM enrichment only on new_applicant_data.json
   - saves new_llm_extend_applicant_data.json

4. insert_new_data.py
   - inserts new_llm_extend_applicant_data.json directly into PostgreSQL
   - does not reset the database
"""

from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent

PIPELINE_STEPS = [
    BASE_DIR / "scrape.py",
    BASE_DIR / "clean_new_data.py",
    BASE_DIR / "run_llm_on_new_data.py",
    BASE_DIR / "insert_new_data.py",
]


def run_step(script_path):
    """
    Run one Python script in the module_2_code directory.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Could not find script: {script_path}")

    print("\n" + "=" * 70)
    print(f"Running: {script_path.name}")
    print("=" * 70)

    subprocess.run(
        [sys.executable, str(script_path)],
        check=True,
        cwd=BASE_DIR
    )


def main():
    print("Starting Pull Data pipeline...")

    for script_path in PIPELINE_STEPS:
        run_step(script_path)

    print("\n" + "=" * 70)
    print("Pull Data pipeline complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()