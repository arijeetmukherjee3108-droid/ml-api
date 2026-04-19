from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import joblib
import numpy as np
import pandas as pd

app = FastAPI()

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# 📦 LOAD MODEL + DATA
# =========================
try:
    model_path = os.path.join(BASE_DIR, "model.pkl")
    data_path = os.path.join(BASE_DIR, "processed_data.csv")
    model = joblib.load(model_path)
    df = pd.read_csv(data_path)
except Exception as e:
    print(f"Error loading model/data: {e}")
    # We'll handle this gracefully so the main app doesn't crash
    model = None
    df = None


# =========================
# 📌 REQUEST MODEL (Fixes 422)
# =========================
class RouteRequest(BaseModel):
    coordinates: List[List[float]]

    # Validate coordinates format
    @classmethod
    def validate(cls, value):
        for point in value.get("coordinates", []):
            if len(point) != 2:
                raise ValueError("Each coordinate must be [lat, lng]")
        return value


# =========================
# 🔥 FEATURE CONFIG
# =========================
try:
    feature_columns = model.get_booster().feature_names
except:
    # fallback (remove non-feature columns manually)
    feature_columns = [
        col for col in df.columns
        if col not in ["target", "label"]
    ]


# =========================
# 📍 FIND NEAREST POINT
# =========================
def find_nearest(lat, lng):
    distances = ((df["lat"] - lat)**2 + (df["lng"] - lng)**2)
    idx = distances.idxmin()
    return df.iloc[idx]


# =========================
# 🧠 FEATURE EXTRACTION
# =========================
def extract_features_from_route(coords):

    features_list = []
    explanations = []

    for lat, lng in coords:

        nearest = find_nearest(lat, lng)

        row = []

        # 🔥 MATCH MODEL FEATURES EXACTLY
        for col in feature_columns:
            if col in nearest:
                row.append(nearest[col])
            else:
                row.append(0)  # fallback

        features_list.append(row)

        # =========================
        # 💡 EXPLANATION ENGINE
        # =========================
        reasons = []

        if "complaint_count" in nearest and nearest["complaint_count"] > 5:
            reasons.append("High complaint area")

        if "distance_to_hotspot_raw" in nearest and nearest["distance_to_hotspot_raw"] < 0.5:
            reasons.append("Near crime hotspot")

        if "is_night" in nearest and nearest["is_night"] == 1:
            reasons.append("Night time risk")

        if "is_forest" in nearest and nearest["is_forest"] == 1:
            reasons.append("Isolated area")

        if "severity" in nearest and nearest["severity"] > 2:
            reasons.append("High severity incidents")

        explanations.append(reasons)

    return np.array(features_list), explanations


# =========================
# 🚀 MAIN API
# =========================
@app.post("/predict")
def predict(data: RouteRequest):

    try:
        coords = data.coordinates

        if not coords:
            raise HTTPException(status_code=400, detail="Coordinates cannot be empty")

        feature_matrix, explanations = extract_features_from_route(coords)

        # 🔍 DEBUG (optional)
        print("Expected features:", len(feature_columns))
        print("Given features:", len(feature_matrix[0]))

        predictions = model.predict(feature_matrix)

        # =========================
        # 🎯 FINAL SCORE
        # =========================
        final_score = int(np.mean(predictions))

        # =========================
        # 📍 SEGMENT DETAILS
        # =========================
        segments = []
        for i, (latlng, pred) in enumerate(zip(coords, predictions)):
            segments.append({
                "lat": latlng[0],
                "lng": latlng[1],
                "risk": int(pred),
                "reasons": explanations[i]
            })

        # =========================
        # 🧠 SUMMARY
        # =========================
        all_reasons = [r for sub in explanations for r in sub]
        summary = list(set(all_reasons)) if all_reasons else ["Low risk area"]

        return {
            "risk": final_score,
            "level": get_label(final_score),
            "summary": summary,
            "segments": segments
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# 🏷️ LABEL MAPPING
# =========================
def get_label(score):
    if score == 0:
        return "SAFE"
    elif score == 1:
        return "MODERATE"
    else:
        return "RISKY"