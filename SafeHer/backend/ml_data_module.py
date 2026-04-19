import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase (Standalone)
# This module is ONLY for the ML team to collect high-resolution raw data.
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase-adminsdk.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Warning: Firebase initialization failed: {e}")
    db = None

def save_raw_data_for_ml(
    lat: float, 
    lng: float, 
    incident_type: str, 
    description: str, 
    suspect_name: str, 
    evidence_url: str,
    ipfs_cid: str
):
    """
    Saves un-hashed, raw metrics into Firebase.
    This data is specifically for the ML models to generate Heatmaps and Risk Scores.
    """
    if db:
        try:
            db.collection('reports').add({
                "lat": lat,
                "lng": lng,
                "incident_type": incident_type,
                "description": description,
                "suspect_name": suspect_name,
                "evidence_url": evidence_url,
                "ipfs_cid": ipfs_cid,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"ML Data Capture Error: {e}")
            return False
    return False
