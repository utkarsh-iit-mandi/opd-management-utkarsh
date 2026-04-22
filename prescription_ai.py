from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from collections import Counter

prescription_bp = Blueprint("prescription_ai", __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["clinic_db"]
col = db["prescriptions"]

# ─────────────────────────────────────────
# 💾 SAVE PRESCRIPTION
# ─────────────────────────────────────────
def save_prescription(symptoms, medicines):
    if not symptoms or not medicines:
        return

    symptoms_list = [s.strip().lower() for s in symptoms.split(",") if s.strip()]

    col.insert_one({
        "symptoms": symptoms_list,
        "medicines": medicines,
        "timestamp": datetime.now()
    })


# ─────────────────────────────────────────
# 🔍 GET SUGGESTIONS
# ─────────────────────────────────────────
@prescription_bp.route("/api/prescription_suggestions")
def get_suggestions():
    symptoms_input = request.args.get("symptoms", "").lower()

    if len(symptoms_input) < 2:
        return jsonify([])

    input_list = [s.strip() for s in symptoms_input.split(",") if s.strip()]

    results = col.find()

    scored = []

    for r in results:
        stored_symptoms = r.get("symptoms", [])
        score = len(set(input_list) & set(stored_symptoms))

        if score > 0:
            scored.append((score, r.get("medicines", [])))

    # Sort by best match
    scored.sort(reverse=True)

    meds = []
    for _, mlist in scored:
        meds.extend(mlist)

    from collections import Counter
    top = [m for m, _ in Counter(meds).most_common(6)]

    return jsonify(top)