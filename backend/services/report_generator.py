"""
report_generator.py
===================
Report generation and dataset enrichment utilities.
Medinote | AI-Powered CRM for Medical Representatives

Functions:
  generate_draft_report(record)                        → formatted str report
  enrich_report_features(record, reports_history)      → enriched record dict
  normalize_visit_record(record)                       → visits_df-compatible dict
"""

from typing import Any, Dict, Optional

import pandas as pd


def generate_draft_report(record: Dict[str, Any]) -> str:
    """
    Auto-fill the rapport_resume template from a corrected record.
    Handles missing/NaN fields gracefully.
    """
    def get(key: str) -> Optional[str]:
        val = record.get(key, None)
        if val is None or pd.isna(val) or str(val).strip() == "":
            return None
        return str(val)

    parts = []
    type_visite = get("type_visite")
    nom_medecin = get("nom_medecin")
    specialite = get("specialite_medecin")
    region = get("region")

    if type_visite and nom_medecin:
        header = f"Visite {type_visite} chez {nom_medecin}"
    elif nom_medecin:
        header = f"Visite chez {nom_medecin}"
    elif type_visite:
        header = f"Visite {type_visite}"
    else:
        header = "Visite médicale"

    if specialite:
        header += f" ({specialite})"
    if region:
        header += f" à {region}"
    parts.append(header + ".")

    medicament = get("medicament")
    indication = get("indication_clean") or get("indication")
    if medicament or indication:
        line = "Produit : " + (medicament or "N/A")
        if indication:
            line += f" | Indication : {indication}"
        parts.append(line + ".")

    objectif = get("objectif_visite")
    if objectif:
        parts.append(f"Objectif : {objectif}.")

    message = get("message_cle")
    if message:
        parts.append(f"Message clé : {message}")

    objection = get("objection_clean") or get("objection")
    if objection:
        parts.append(f"Objection : {objection}.")

    reponse = get("reponse")
    if reponse:
        parts.append(f"Réponse : {reponse}")

    commentaire = get("commentaire_visite")
    if commentaire:
        parts.append(f"Commentaire : {commentaire}")

    niveau = get("niveau_interet")
    if niveau:
        parts.append(f"Intérêt : {niveau}/5.")

    action = get("prochaine_action")
    if action:
        parts.append(f"Action suivante : {action}")

    return "\n".join(parts).strip() if parts else "Note médicale indisponible."


def enrich_report_features(record: Dict[str, Any], reports_history: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute all engineered features needed for delegue_reports_clean_features.csv.
    Aggregates from existing history and appends the current record's contribution.
    """
    out = dict(record)

    doctor_mask    = reports_history["nom_medecin"].astype(str).str.lower()    == str(record["nom_medecin"]).lower()
    spec_mask      = reports_history["specialite_medecin"].astype(str).str.lower() == str(record["specialite_medecin"]).lower()
    product_mask   = reports_history["medicament"].astype(str).str.lower()     == str(record["medicament"]).lower()
    objective_mask = reports_history["objectif_visite"].astype(str).str.lower()== str(record["objectif_visite"]).lower()

    def _safe_mean(mask, new_val):
        vals = pd.concat([reports_history.loc[mask, "niveau_interet"], pd.Series([int(new_val)])])
        return float(vals.mean())

    interest = int(record.get("niveau_interet", 0))

    out["resume_visite"]          = generate_draft_report(record)
    out["high_interest"]          = int(interest >= 4)
    out["doctor_visit_count"]     = int(doctor_mask.sum()) + 1
    out["doctor_avg_interest"]    = _safe_mean(doctor_mask,    interest)
    out["specialty_visit_count"]  = int(spec_mask.sum()) + 1
    out["specialty_avg_interest"] = _safe_mean(spec_mask,      interest)
    out["product_visit_count"]    = int(product_mask.sum()) + 1
    out["product_avg_interest"]   = _safe_mean(product_mask,   interest)
    out["objective_avg_interest"] = _safe_mean(objective_mask, interest)

    out["message_cle_len"]          = len(str(record.get("message_cle", "")))
    out["message_cle_wc"]           = len(str(record.get("message_cle", "")).split())
    out["reponse_len"]              = len(str(record.get("reponse", "")))
    out["reponse_wc"]               = len(str(record.get("reponse", "")).split())
    out["commentaire_visite_len"]   = len(str(record.get("commentaire_visite", "")))
    out["commentaire_visite_wc"]    = len(str(record.get("commentaire_visite", "")).split())
    out["resume_visite_len"]        = len(out["resume_visite"])
    out["resume_visite_wc"]         = len(out["resume_visite"].split())

    comment   = str(record.get("commentaire_visite", "")).lower()
    objection = str(record.get("objection", "")).lower()
    out["flag_retissant"]  = int("retissant" in comment or "rétissant" in comment)
    out["flag_satisfait"]  = int("satisfait" in comment)
    out["flag_interesse"]  = int("intéressé" in comment or "interesse" in comment)
    out["flag_objection"]  = int(
        bool(str(record.get("objection", "")).strip())
        and objection not in {"aucune", "sans objection"}
    )
    out["engagement_score"] = float(
        interest * 100
        + out["doctor_visit_count"]
        + out["specialty_visit_count"]
        + out["product_visit_count"]
    )
    return out


def normalize_visit_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a record for insertion into visits_ready_clean_FR.csv.
    Adds _clean columns and both report fields.
    """
    record = dict(record)
    record["region_clean"]            = record.get("region", "")
    record["indication_clean"]        = record.get("indication", "")
    record["objection_clean"]         = record.get("objection", "")
    draft = generate_draft_report(record)
    record["rapport_resume_original"] = draft
    record["rapport_resume"]          = draft
    return record
