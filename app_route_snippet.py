# ─────────────────────────────────────────────────────────────
# ADD THIS ROUTE TO YOUR app.py
# Medicines autocomplete API  →  GET /api/medicines?q=para
# ─────────────────────────────────────────────────────────────

@app.route("/api/medicines")
def api_medicines():
    """
    Returns up to 10 medicine suggestions as JSON.
    Called by the frontend autocomplete via fetch().
    """
    from flask import jsonify, request as req
    import sqlite3

    query = req.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Search: starts-with match first, then contains match
    pattern = f"{query}%"
    contains = f"%{query}%"

    c.execute("""
        SELECT name, composition FROM medicines
        WHERE name LIKE ? COLLATE NOCASE
        LIMIT 7
    """, (pattern,))
    starts_with = c.fetchall()

    # Fill remaining slots with contains-match
    needed = 10 - len(starts_with)
    already = [r[0] for r in starts_with]
    placeholders = ",".join("?" * len(already)) if already else "''"
    c.execute(f"""
        SELECT name, composition FROM medicines
        WHERE name LIKE ? COLLATE NOCASE
          AND name NOT IN ({placeholders})
        LIMIT ?
    """, [contains] + already + [needed])
    contains_results = c.fetchall()
    conn.close()

    results = starts_with + contains_results
    return jsonify([
        {"name": r[0], "composition": r[1]}
        for r in results
    ])
