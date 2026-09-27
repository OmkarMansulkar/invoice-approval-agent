"""
Run this once before your demo to pre-populate the database with a few
processed invoices, so you have real data to show even before running any
live requests.

Usage: python seed_demo_data.py
"""
import glob
import os

from app.db.database import init_db
from app.agents.graph import run_invoice_pipeline

# Resolve relative to this file's location, not the caller's current working
# directory -- so this still works regardless of which folder you run it from.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_GLOB = os.path.join(SCRIPT_DIR, "sample_invoices", "*.txt")

if __name__ == "__main__":
    init_db()
    sample_files = sorted(glob.glob(SAMPLES_GLOB))
    if not sample_files:
        print(f"No sample invoices found at {SAMPLES_GLOB} -- check the path.")
    for path in sample_files:
        with open(path) as f:
            raw_text = f.read()
        result = run_invoice_pipeline(raw_text)
        print(f"{path} -> invoice_id={result.get('invoice_id')} decision={result.get('decision')}")
