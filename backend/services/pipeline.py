"""
pipeline.py
===========
End-to-end pipeline combining Task 4 (text correction) and Task 5 (integrity control).
Medinote | AI-Powered CRM for Medical Representatives

Main entry points:
  run_full_pipeline(record, visits_history, reports_history)
      → validates + generates draft report for a structured record

  append_if_valid(pipeline_result, visits_history, reports_history)
      → appends PASS records to both DataFrames

For raw free-text input from users, call text_correction.parse_and_correct_raw_note()
first, then pass the extracted record to run_full_pipeline().
"""

from typing import Any, Dict, Tuple

import pandas as pd

from services.integrity_control import REJECTION_THRESHOLD, validate_record
from services.report_generator import (
    enrich_report_features,
    generate_draft_report,
    normalize_visit_record,
)


def run_full_pipeline(
    record: Dict[str, Any],
    visits_history: pd.DataFrame,
    reports_history: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Run integrity check + draft report generation on a structured record.

    Text correction (Task 4) must be applied upstream via:
      - text_correction.parse_and_correct_raw_note()  — for raw free-text input
      - text_correction.correct_existing_record()      — for structured records

    Parameters
    ----------
    record          : dict          — structured visit record (14 fields)
    visits_history  : pd.DataFrame  — existing visits dataset (for duplicate check)
    reports_history : pd.DataFrame  — existing reports dataset

    Returns
    -------
    dict with keys:
        status           : 'PASS' | 'REJECT'
        integrity_score  : int   (0-100)
        confidence_score : int   (0-100, set upstream by Task 4)
        final_score      : int   (0-100)
        alerts           : list of alert dicts
        corrections_log  : list  (populated upstream by Task 4)
        corrected_record : dict
        draft_report     : str
    """
    t5 = validate_record(record, reports_history)

    corrected = dict(record)
    corrected["indication_clean"] = corrected.get("indication", corrected.get("indication_clean", ""))
    corrected["objection_clean"]  = corrected.get("objection",  corrected.get("objection_clean",  ""))
    corrected["region_clean"]     = corrected.get("region",     corrected.get("region_clean",     ""))

    draft = generate_draft_report(corrected)
    corrected["rapport_resume_original"] = draft
    corrected["rapport_resume"]          = draft

    combined_score = t5["quality_score"]
    final_status   = "PASS" if combined_score >= REJECTION_THRESHOLD and t5["status"] == "PASS" else "REJECT"

    return {
        "status":           final_status,
        "integrity_score":  t5["quality_score"],
        "confidence_score": 100,
        "final_score":      combined_score,
        "alerts":           t5["alerts"],
        "corrections_log":  [],
        "language_flags":   {},
        "corrected_record": corrected,
        "draft_report":     draft,
    }


def append_if_valid(
    pipeline_result: Dict[str, Any],
    visits_history: pd.DataFrame,
    reports_history: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Append a validated record to both datasets in memory.
    Only appends if pipeline_result['status'] == 'PASS'.

    Returns updated (visits_df, reports_df) tuple.
    """
    new_visits  = visits_history.copy()
    new_reports = reports_history.copy()

    if pipeline_result["status"] != "PASS":
        print("❌ Record rejected — not appended.")
        return new_visits, new_reports

    corrected  = pipeline_result["corrected_record"]
    visit_row  = normalize_visit_record(corrected)
    report_row = enrich_report_features(corrected, new_reports)

    visit_row  = pd.DataFrame([visit_row]).reindex(columns=new_visits.columns)
    report_row = pd.DataFrame([report_row]).reindex(columns=new_reports.columns)

    new_visits  = pd.concat([new_visits,  visit_row],  ignore_index=True)
    new_reports = pd.concat([new_reports, report_row], ignore_index=True)

    print("✅ Record appended to both datasets.")
    return new_visits, new_reports
