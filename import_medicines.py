"""
Run this ONCE to import the medicines dataset into your clinic database.

Usage:
    python import_medicines.py

Place this file next to your app.py and the CSV file in the same folder.
"""

import csv
import sqlite3
import os

DB_PATH  = "database.db"
CSV_PATH = "A_Z_medicines_dataset_of_India 2.csv"

def import_medicines():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            composition TEXT
        )
    """)

    # Full-text search index for fast LIKE queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_med_name ON medicines(name COLLATE NOCASE)")

    # Skip if already populated
    existing = c.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    if existing > 0:
        print(f"Medicines table already has {existing} records. Skipping import.")
        conn.close()
        return

    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            comp = r["short_composition1"].strip()
            if r["short_composition2"].strip():
                comp += " + " + r["short_composition2"].strip()
            rows.append((int(r["id"]), r["name"].strip(), comp))

    c.executemany("INSERT OR IGNORE INTO medicines VALUES (?, ?, ?)", rows)
    conn.commit()
    print(f"✅ Imported {c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]} medicines.")
    conn.close()

if __name__ == "__main__":
    import_medicines()
