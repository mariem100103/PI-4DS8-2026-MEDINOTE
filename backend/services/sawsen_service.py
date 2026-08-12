from fastapi import APIRouter, HTTPException
import joblib
import pandas as pd
import numpy as np
import os

router = APIRouter()

# Chemins des modèles
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Charger les modèles (lazy load pour éviter de bloquer le démarrage de l'API
# si une dépendance optionnelle des modèles n'est pas installée).
kmeans = None
model = None
scaler = None
le_dict = None
model_load_error = None


def _load_models():
    global kmeans, model, scaler, le_dict, model_load_error
    if model_load_error is not None:
        raise model_load_error
    if all(x is not None for x in (kmeans, model, scaler, le_dict)):
        return

    try:
        kmeans = joblib.load(os.path.join(MODELS_DIR, "sawsen_kmeans.pkl"))
        model = joblib.load(os.path.join(MODELS_DIR, "sawsen_lr_model.pkl"))
        scaler = joblib.load(os.path.join(MODELS_DIR, "sawsen_scaler.pkl"))
        le_dict = joblib.load(os.path.join(MODELS_DIR, "sawsen_encoders.pkl"))
    except Exception as exc:
        model_load_error = exc
        raise

persona_names = {
    0: "🟢 Highly Receptive",
    1: "🔴 High Resistance",
    2: "🟠 Low Engagement"
}

strategy_map = {
    "🟢 Highly Receptive": "Consolidate relationship — share new clinical data and propose a follow-up visit.",
    "🔴 High Resistance":  "Handle objections — share tolerance evidence and schedule a short focused visit.",
    "🟠 Low Engagement":   "Re-engage — offer product trial, invite to medical event, or escalate to manager.",
}

objection_map = {
    "🟢 Highly Receptive": "Occasional questions on clinical studies",
    "🔴 High Resistance":  "Tolerance / side effects / competition",
    "🟠 Low Engagement":   "Availability / interest in new products",
}

@router.post("/predict")
async def predict_persona(data: dict):
    try:
        _load_models()
        features = [
            data.get("doctor_visit_count", 0),
            data.get("specialty_visit_count", 0),
            data.get("product_visit_count", 0),
            data.get("reponse_wc", 0),
            data.get("reponse_len", 0),
            data.get("resume_visite_wc", 0),
            data.get("commentaire_visite_wc", 0),
            data.get("specialite_medecin_enc", 0),
            data.get("medicament_enc", 0),
            data.get("type_visite_enc", 0),
            data.get("objectif_visite_enc", 0),
        ]
        X       = scaler.transform([features])
        cluster = int(kmeans.predict(X)[0])
        proba   = float(model.predict_proba(
                      np.append(X[0], cluster).reshape(1, -1))[0][1])
        persona = persona_names.get(cluster, "Unknown")

        return {
            "persona"              : persona,
            "strategy"             : strategy_map.get(persona, ""),
            "objection"            : objection_map.get(persona, ""),
            "high_interest_proba"  : round(proba * 100, 1),
            "cluster"              : cluster
        }
    except ModuleNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Model dependency missing: {e}. Install missing package(s) and retry."
        )
    except Exception as e:
        return {"error": str(e)}

@router.get("/health")
async def health():
    return {"status": "ok", "module": "HCP Persona — Sawsen"}