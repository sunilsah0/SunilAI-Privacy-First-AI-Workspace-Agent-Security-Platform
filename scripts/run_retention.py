"""Deletes conversations older than each person's chosen retention period.
Run from the project folder:  python scripts\\run_retention.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from services.api.app.retention import run_retention  # noqa: E402

print(f"Deleted {run_retention()} old conversation(s).")