"""
routers/integrity_router.py
=================================
Integrity + Quality + Report endpoints for Medinote.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import importlib

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.pipeline import run_full_pipeline
from services.integrity_control import validate_record
from services.quality_scorer import compute_report_quality_score
from services.report_generator import generate_draft_report, enrich_report_features
from services.batch_processor import run_batch

router = APIRouter(prefix="/integrity", tags=["Integrity"])


class RawNoteInput(BaseModel):
    raw_note: str


_BASE_DIR = Path(__file__).resolve().parents[1]
_MODELS_DIR = _BASE_DIR / "models"
_VISITS_PATH = _MODELS_DIR / "visits_ready_clean_FR.csv"
_REPORTS_PATH = _MODELS_DIR / "delegue_reports_clean_features.csv"

_visits_cache: pd.DataFrame | None = None
_reports_cache: pd.DataFrame | None = None


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _load_histories() -> tuple[pd.DataFrame, pd.DataFrame]:
    global _visits_cache, _reports_cache
    if _visits_cache is None:
        _visits_cache = _safe_read_csv(_VISITS_PATH)
    if _reports_cache is None:
        _reports_cache = _safe_read_csv(_REPORTS_PATH)
    return _visits_cache, _reports_cache


def _parse_and_correct(raw_note: str) -> dict:
    try:
        text_correction = importlib.import_module("services.text_correction")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Module text_correction introuvable: {exc}",
        )
    if not hasattr(text_correction, "parse_and_correct_raw_note"):
        raise HTTPException(
            status_code=500,
            detail="text_correction.parse_and_correct_raw_note indisponible",
        )
    return text_correction.parse_and_correct_raw_note(raw_note)


def _normalize_record(record: dict) -> dict:
    normalized = dict(record)
    normalized["indication_clean"] = normalized.get("indication", "")
    normalized["objection_clean"] = normalized.get("objection", "")
    normalized["region_clean"] = normalized.get("region", "")
    return normalized


@router.post("/check")
async def check_integrity(payload: RawNoteInput):
    if not payload.raw_note or not payload.raw_note.strip():
        raise HTTPException(status_code=400, detail="Le champ 'raw_note' est vide.")

    parsed = _parse_and_correct(payload.raw_note)
    record = parsed.get("record")
    if not isinstance(record, dict):
        raise HTTPException(status_code=500, detail="Record corrigé invalide.")

    record = _normalize_record(record)
    visits_df, reports_df = _load_histories()
    pipeline_result = run_full_pipeline(record, visits_df, reports_df)
    pipeline_result["confidence_score"] = parsed.get("confidence_score", 100)
    pipeline_result["corrections_log"] = parsed.get("corrections_log", [])

    integrity_score = int(pipeline_result.get("integrity_score", 0))
    penalty_score = max(0, 100 - integrity_score)
    failed_fields = sorted({
        a.get("field") for a in pipeline_result.get("alerts", [])
        if a.get("severity") == "ERROR" and a.get("field")
    })

    return {
        "status": pipeline_result.get("status"),
        "integrity_score": integrity_score,
        "penalty_score": penalty_score,
        "failed_fields": failed_fields,
        "alerts": pipeline_result.get("alerts", []),
        "corrected_record": pipeline_result.get("corrected_record", {}),
    }


@router.post("/summary")
async def summary(payload: RawNoteInput):
    if not payload.raw_note or not payload.raw_note.strip():
        raise HTTPException(status_code=400, detail="Le champ 'raw_note' est vide.")

    parsed = _parse_and_correct(payload.raw_note)
    record = parsed.get("record")
    if not isinstance(record, dict):
        raise HTTPException(status_code=500, detail="Record corrigé invalide.")

    record = _normalize_record(record)
    visits_df, reports_df = _load_histories()
    pipeline_result = run_full_pipeline(record, visits_df, reports_df)

    integrity_score = int(pipeline_result.get("integrity_score", 0))
    quality = compute_report_quality_score(
        record,
        integrity_score=integrity_score,
        confidence_score=parsed.get("confidence_score", 100),
        alerts=pipeline_result.get("alerts", []),
    )

    draft_report = pipeline_result.get("draft_report") if pipeline_result.get("status") == "PASS" else ""
    failed_fields = sorted({
        a.get("field") for a in pipeline_result.get("alerts", [])
        if a.get("severity") == "ERROR" and a.get("field")
    })

    return {
        "status": pipeline_result.get("status"),
        "integrity_score": integrity_score,
        "penalty_score": max(0, 100 - integrity_score),
        "failed_fields": failed_fields,
        "alerts": pipeline_result.get("alerts", []),
        "quality_score": quality["quality_score"],
        "grade": quality["grade"],
        "recommendations": quality["recommendations"],
        "draft_report": draft_report,
        "corrected_record": pipeline_result.get("corrected_record", {}),
        "corrections_log": parsed.get("corrections_log", []),
        "standardisations": parsed.get("standardisations", []),
    }


@router.post("/score")
async def score_quality(payload: RawNoteInput):
    if not payload.raw_note or not payload.raw_note.strip():
        raise HTTPException(status_code=400, detail="Le champ 'raw_note' est vide.")

    parsed = _parse_and_correct(payload.raw_note)
    record = parsed.get("record")
    if not isinstance(record, dict):
        raise HTTPException(status_code=500, detail="Record corrigé invalide.")

    _, reports_df = _load_histories()
    integrity = validate_record(record, reports_df)

    quality = compute_report_quality_score(
        record,
        integrity_score=integrity["quality_score"],
        confidence_score=parsed.get("confidence_score", 100),
        alerts=integrity["alerts"],
    )

    return {
        "quality_score": quality["quality_score"],
        "grade": quality["grade"],
        "recommendations": quality["recommendations"],
        "breakdown": quality["breakdown"],
    }


@router.post("/report")
async def generate_report(payload: RawNoteInput):
    if not payload.raw_note or not payload.raw_note.strip():
        raise HTTPException(status_code=400, detail="Le champ 'raw_note' est vide.")

    parsed = _parse_and_correct(payload.raw_note)
    record = parsed.get("record")
    if not isinstance(record, dict):
        raise HTTPException(status_code=500, detail="Record corrigé invalide.")

    record = _normalize_record(record)

    draft = generate_draft_report(record)
    return {"draft_report": draft}


@router.post("/append")
async def append_report(payload: RawNoteInput):
    global _reports_cache
    if not payload.raw_note or not payload.raw_note.strip():
        raise HTTPException(status_code=400, detail="Le champ 'raw_note' est vide.")

    parsed = _parse_and_correct(payload.raw_note)
    record = parsed.get("record")
    if not isinstance(record, dict):
        raise HTTPException(status_code=500, detail="Record corrigé invalide.")

    record = _normalize_record(record)
    visits_df, reports_df = _load_histories()
    pipeline_result = run_full_pipeline(record, visits_df, reports_df)

    if pipeline_result.get("status") != "PASS":
        raise HTTPException(status_code=400, detail="La note n'est pas valide (status REJECT).")

    report_row = enrich_report_features(record, reports_df)
    report_row_df = pd.DataFrame([report_row])
    if not reports_df.empty:
        report_row_df = report_row_df.reindex(columns=reports_df.columns)
    new_reports = pd.concat([reports_df, report_row_df], ignore_index=True)
    if not new_reports.empty:
        new_reports.to_csv(_REPORTS_PATH, index=False)
        _reports_cache = new_reports

    return {"appended": True, "reports_total": int(new_reports.shape[0])}


@router.post("/batch")
async def batch_process(file: UploadFile = File(...)):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    suffix = Path(file.filename).suffix.lower()
    if suffix != ".csv":
        raise HTTPException(status_code=400, detail="Veuillez fournir un fichier CSV.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier CSV vide.")

    visits_df, reports_df = _load_histories()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        results_df, _, _ = run_batch(
            input_csv=tmp_path,
            visits_df=visits_df,
            reports_df=reports_df,
            delay_seconds=0.2,
            save_output=False,
        )
        processed = int(results_df.shape[0])
        return {"processed": processed}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
