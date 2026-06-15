import os
import sys
from pathlib import Path

# Add module_4/src to the Python path so Sphinx can import app.py, db_utils.py, etc.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

project = "Grad Cafe Analysis App"
copyright = "2026, Karunya Narayanamurthy"
author = "Karunya Narayanamurthy"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]