"""
batch_processor.py
==================
Batch Processing Mode — process many raw notes from a CSV file at once.
Medinote | AI-Powered CRM for Medical Representatives

Input CSV format (one column required):
    raw_note  — free-text visit note written by the delegate

The processor:
  1. Reads each raw note from the CSV
  2. Calls Groq to extract + correct all fields (Task 4)
  3. Validates integrity (Task 5)
  4. Computes Report Quality Score (Task 6)
  5. Appends PASS records to the datasets
  6. Saves a full results CSV with scores, alerts, and corrections

Usage (from terminal):
    python batch_processor.py --input notes.csv --visits visits_ready_clean_FR.csv --reports delegue_reports_clean_features.csv

Usage (from Python):
    from batch_processor import run_batch
    results_df = run_batch("notes.csv", visits_df, reports_df)
"""

import argparse
import time
from pathlib import Path

import pandas as pd

import importlib

from services.integrity_control import validate_record
from services.pipeline import append_if_valid, run_full_pipeline
from services.quality_scorer import compute_report_quality_score


# ─────────────────────────────────────────────────────────────────────────────
# CORE BATCH FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def run_batch(
    input_csv: str,
    visits_df: pd.DataFrame,
    reports_df: pd.DataFrame,
    delay_seconds: float = 0.5,
    save_output: bool = True,
    output_path: str = "batch_results.csv",
) -> pd.DataFrame:
    """
    Process all raw notes in input_csv through the full Medinote pipeline.

    Parameters
    ----------
    input_csv      : str            — path to CSV with a 'raw_note' column
    visits_df      : pd.DataFrame   — existing visits dataset (updated in-place)
    reports_df     : pd.DataFrame   — existing reports dataset (updated in-place)
    delay_seconds  : float          — pause between API calls (avoids rate limiting)
    save_output    : bool           — whether to save results CSV
    output_path    : str            — where to save the results

    Returns
    -------
    pd.DataFrame with columns:
        raw_note, status, quality_score, grade,
        integrity_score, confidence_score, richness_score,
        alert_count, correction_count, draft_report,
        recommendations, errors
    """
    input_df = pd.read_csv(input_csv)

    if "raw_note" not in input_df.columns:
        raise ValueError(
            f"Input CSV must have a 'raw_note' column. Found: {list(input_df.columns)}"
        )

    notes    = input_df["raw_note"].dropna().tolist()
    total    = len(notes)
    results  = []

    try:
        text_correction = importlib.import_module("services.text_correction")
        parse_and_correct_raw_note = text_correction.parse_and_correct_raw_note
    except Exception as exc:
        raise ValueError(f"Module text_correction introuvable: {exc}")

    print(f"{'='*55}")
    print(f"  MEDINOTE — Batch Processing")
    print(f"  {total} notes to process")
    print(f"{'='*55}")

    for i, raw_note in enumerate(notes, 1):
        print(f"\n[{i}/{total}] Processing note: {str(raw_note)[:60]}...")
        row = {"raw_note": raw_note, "errors": ""}

        try:
            # Step 1 — Task 4: extract + correct
            parsed     = parse_and_correct_raw_note(str(raw_note))
            record     = parsed["record"]
            confidence = parsed["confidence_score"]
            corrections= parsed["corrections_log"]

            # Step 2 — Task 5: integrity check
            t5 = validate_record(record, reports_df)

            # Step 3 — Task 6: quality score
            qs = compute_report_quality_score(
                record,
                integrity_score=t5["quality_score"],
                confidence_score=confidence,
                alerts=t5["alerts"],
            )

            # Step 4 — pipeline: generate report + decide
            record["indication_clean"] = record.get("indication", "")
            record["objection_clean"]  = record.get("objection",  "")
            record["region_clean"]     = record.get("region",     "")

            pipeline_result = run_full_pipeline(record, visits_df, reports_df)
            pipeline_result["confidence_score"] = confidence
            pipeline_result["corrections_log"]  = corrections

            # Step 5 — append if PASS
            if pipeline_result["status"] == "PASS":
                visits_df, reports_df = append_if_valid(pipeline_result, visits_df, reports_df)

            # Collect results
            row.update({
                "status":           pipeline_result["status"],
                "quality_score":    qs["quality_score"],
                "grade":            qs["grade"],
                "integrity_score":  t5["quality_score"],
                "confidence_score": confidence,
                "richness_score":   qs["breakdown"]["richness_score"],
                "alert_count":      len(t5["alerts"]),
                "correction_count": len(corrections),
                "draft_report":     pipeline_result["draft_report"],
                "recommendations":  " | ".join(qs["recommendations"]),
                "nom_medecin":      record.get("nom_medecin", ""),
                "medicament":       record.get("medicament", ""),
                "region":           record.get("region", ""),
                "type_visite":      record.get("type_visite", ""),
                "niveau_interet":   record.get("niveau_interet", 0),
            })

            status_icon = "✅" if pipeline_result["status"] == "PASS" else "❌"
            print(f"   {status_icon} {pipeline_result['status']} | Quality: {qs['quality_score']}/100 ({qs['grade']})")

        except Exception as e:
            row.update({
                "status": "ERROR", "quality_score": 0, "grade": "F",
                "integrity_score": 0, "confidence_score": 0, "richness_score": 0,
                "alert_count": 0, "correction_count": 0,
                "draft_report": "", "recommendations": "", "errors": str(e),
            })
            print(f"   ⚠️  Error: {e}")

        results.append(row)

        # Polite pause between API calls
        if i < total:
            time.sleep(delay_seconds)

    results_df = pd.DataFrame(results)
    _print_batch_summary(results_df)

    if save_output:
        results_df.to_csv(output_path, index=False)
        print(f"\n✅ Results saved to: {output_path}")

    return results_df, visits_df, reports_df


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def _print_batch_summary(results_df: pd.DataFrame):
    total    = len(results_df)
    passed   = (results_df["status"] == "PASS").sum()
    rejected = (results_df["status"] == "REJECT").sum()
    errors   = (results_df["status"] == "ERROR").sum()
    avg_q    = results_df["quality_score"].mean()

    print(f"\n{'='*55}")
    print(f"  MEDINOTE — Batch Summary")
    print(f"{'='*55}")
    print(f"  Total processed  : {total}")
    print(f"  ✅ PASS          : {passed}  ({100*passed/total:.1f}%)")
    print(f"  ❌ REJECT        : {rejected}  ({100*rejected/total:.1f}%)")
    if errors:
        print(f"  ⚠️  ERRORS       : {errors}")
    print(f"  Avg quality score: {avg_q:.1f}/100")
    print(f"\n  Grade distribution:")
    if "grade" in results_df.columns:
        for grade in ["A", "B", "C", "D", "F"]:
            count = (results_df["grade"] == grade).sum()
            bar   = "█" * count
            print(f"    {grade}  {bar}  ({count})")
    print(f"{'='*55}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Medinote Batch Processor")
    parser.add_argument("--input",   required=True,  help="Path to input CSV with 'raw_note' column")
    parser.add_argument("--visits",  required=False, help="Path to visits_ready_clean_FR.csv")
    parser.add_argument("--reports", required=False, help="Path to delegue_reports_clean_features.csv")
    parser.add_argument("--output",  default="batch_results.csv", help="Output CSV path")
    parser.add_argument("--delay",   type=float, default=0.5, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    # Load datasets
    visits_df  = pd.read_csv(args.visits)  if args.visits  else pd.DataFrame()
    reports_df = pd.read_csv(args.reports) if args.reports else pd.DataFrame()

    results_df, updated_visits, updated_reports = run_batch(
        input_csv=args.input,
        visits_df=visits_df,
        reports_df=reports_df,
        delay_seconds=args.delay,
        save_output=True,
        output_path=args.output,
    )

    # Optionally save updated datasets
    if args.visits and not updated_visits.empty:
        out = args.visits.replace(".csv", "_updated.csv")
        updated_visits.to_csv(out, index=False)
        print(f"✅ Updated visits saved to: {out}")

    if args.reports and not updated_reports.empty:
        out = args.reports.replace(".csv", "_updated.csv")
        updated_reports.to_csv(out, index=False)
        print(f"✅ Updated reports saved to: {out}")
