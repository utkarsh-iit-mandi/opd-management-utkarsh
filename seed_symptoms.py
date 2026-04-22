from pymongo import MongoClient
import csv

client = MongoClient("mongodb://localhost:27017/")
db = client["clinic_db"]
col = db["symptoms"]

file_path = "Final_Augmented_dataset_Diseases_and_Symptoms.csv"

with open(file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        # ⚠️ Adjust column name if needed
        symptoms = row.get("Symptoms") or row.get("symptoms")

        if not symptoms:
            continue

        # Split multiple symptoms
        parts = [s.strip().lower() for s in symptoms.split(",") if s.strip()]

        for sym in parts:
            col.update_one(
                {"symptom": sym},
                {"$inc": {"count": 1}},
                upsert=True
            )

print("✅ Symptoms imported successfully!")