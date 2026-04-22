"""
medicines_api.py
────────────────
Drop this file next to app.py.

Then add these TWO lines to app.py:

    from medicines_api import medicines_bp, setup_medicines_db
    app.register_blueprint(medicines_bp)

Then call setup once (add inside your if __name__ == '__main__': block or just run manually):

    python medicines_api.py

That's it. The autocomplete will work.
"""

import csv, os, sqlite3
from flask import Blueprint, jsonify, request

# ── Config ─────────────────────────────────────────────────────
DB_PATH  = os.path.join(os.path.dirname(__file__), "database.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "A_Z_medicines_dataset_of_India_2.csv")

# ── Blueprint ──────────────────────────────────────────────────
medicines_bp = Blueprint("medicines", __name__)

@medicines_bp.route("/api/medicines")
def api_medicines():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # starts-with first (higher relevance), then contains
    starts  = f"{q}%"
    contains = f"%{q}%"

    c.execute("""
        SELECT name, composition FROM medicines
        WHERE name LIKE ? COLLATE NOCASE
        LIMIT 6
    """, (starts,))
    rows = c.fetchall()

    if len(rows) < 10:
        done = [r[0] for r in rows]
        placeholders = ",".join("?" * len(done)) if done else "NULL"
        c.execute(f"""
            SELECT name, composition FROM medicines
            WHERE name LIKE ? COLLATE NOCASE
              AND name NOT IN ({placeholders})
            LIMIT ?
        """, [contains] + done + [10 - len(rows)])
        rows += c.fetchall()

    conn.close()
    return jsonify([{"name": r[0], "composition": r[1]} for r in rows])


# ── DB Setup (run once) ────────────────────────────────────────
def setup_medicines_db():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            composition TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_med_name ON medicines(name COLLATE NOCASE)")

    count = c.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    if count > 0:
        print(f"Medicines already loaded ({count} records). Skipping.")
        conn.close()
        return

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}")
        print("Place A_Z_medicines_dataset_of_India_2.csv next to app.py")
        conn.close()
        return

    print("Importing medicines... (this takes ~10 seconds)")
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            comp = r["short_composition1"].strip()
            if r["short_composition2"].strip():
                comp += " + " + r["short_composition2"].strip()
            rows.append((r["name"].strip(), comp))

    c.executemany("INSERT INTO medicines (name, composition) VALUES (?,?)", rows)
    conn.commit()
    print(f"Done. {c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]} medicines loaded.")
    conn.close()


# ── Run directly to populate DB ────────────────────────────────
if __name__ == "__main__":
    setup_medicines_db()
