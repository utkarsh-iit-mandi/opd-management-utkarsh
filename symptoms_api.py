from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime

symptoms_bp = Blueprint("symptoms", __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["clinic_db"]
symptoms_col = db["symptoms"]

# ─────────────────────────────────────────
# 🔍 SEARCH API
# ─────────────────────────────────────────
@symptoms_bp.route("/api/symptoms")
def search_symptoms():
    q = request.args.get("q", "").strip()

    if len(q) < 2:
        return jsonify([])

    results = symptoms_col.find(
        {"symptom": {"$regex": q, "$options": "i"}},
        {"_id": 0}
    ).sort("count", -1).limit(8)

    return jsonify([r["symptom"] for r in results])


# ─────────────────────────────────────────
# 💾 SAVE / LEARN SYMPTOMS
# ─────────────────────────────────────────
def save_symptoms(symptoms_text):
    if not symptoms_text:
        return

    parts = [s.strip().lower() for s in symptoms_text.split(",") if s.strip()]

    for sym in parts:
        symptoms_col.update_one(
            {"symptom": sym},
            {
                "$inc": {"count": 1},
                "$set": {"last_used": datetime.now()}
            },
            upsert=True
        )