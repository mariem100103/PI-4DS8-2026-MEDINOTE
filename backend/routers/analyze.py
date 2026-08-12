# ================================================================
# routers/analyze.py — CRM Médical · FastAPI
# ================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
from services.extraction_service import (
    analyze, load_data, load_trained_models, split_into_notes
)

router = APIRouter(prefix="/analyze", tags=["Analyse"])


class AnalyzeRequest(BaseModel):
    text: str


class MultiAnalyzeRequest(BaseModel):
    text: str
    split_notes: bool = False


def _to_json_safe(value):
    """Convertit récursivement les types numpy en types JSON natifs."""
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, set):
        return [_to_json_safe(v) for v in sorted(value)]
    if isinstance(value, np.generic):
        return value.item()
    return value


@router.post("/text")
async def analyze_text(req: AnalyzeRequest):
    """Analyse une note médicale en texte brut."""
    if not req.text or len(req.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texte trop court.")
    df, _ = load_data()
    models = load_trained_models()
    result = analyze(req.text, models=models, df=df)
    return _to_json_safe(result)


@router.post("/multi")
async def analyze_multi(req: MultiAnalyzeRequest):
    """Analyse un texte contenant plusieurs notes/visites (ex: PDF multi-pages)."""
    if not req.text or len(req.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texte trop court.")
    df, _ = load_data()
    models = load_trained_models()

    notes = split_into_notes(req.text) if req.split_notes else [req.text]
    results = []
    for note in notes:
        r = analyze(note, models=models, df=df)
        results.append(_to_json_safe(r))

    return {
        "count": len(results),
        "notes": results,
        "summary": {
            "all_drugs":   sorted({d for r in results for d in r["Médicaments"]}),
            "all_doctors": sorted({m for r in results for m in r["Médecins"]}),
            "positive":    sum(1 for r in results if r["Sentiment"] == "positif"),
            "negative":    sum(1 for r in results if r["Sentiment"] == "négatif"),
        }
    }
