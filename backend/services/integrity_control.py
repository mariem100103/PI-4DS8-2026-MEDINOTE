"""
integrity_control.py
====================
Task 5 — Data Integrity & Completeness Control
Medinote | AI-Powered CRM for Medical Representatives

Checks each visit record for:
  1. Completeness   — required fields present and non-empty
  2. Valid values   — categorical fields match the allowed set
  3. Business rules — type_visite / objectif_visite alignment
  4. Contradictions — semantic conflicts between fields
  5. Text length    — free-text fields meet minimum word counts
  6. Duplicates     — fuzzy match against existing records

Returns:
  quality_score : int  (0-100)
  alerts        : list of dicts { field, rule, severity, message }
  status        : 'PASS' | 'REJECT'
"""

from difflib import SequenceMatcher
from typing import Any, Dict, List

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "region", "nom_medecin", "specialite_medecin", "medicament",
    "indication", "type_visite", "objectif_visite", "message_cle",
    "objection", "reponse", "niveau_interet", "prochaine_action",
    "commentaire_visite", "gadget",
]

REQUIRED_FIELDS_LIGHT = [
    "nom_medecin",
    "specialite_medecin",
    "medicament",
    "commentaire_visite",
]

VALID_VALUES = {
    "type_visite":        {"Prospection", "Suivi", "Lancement"},
    "objectif_visite":    {"Promouvoir", "Visite de routine", "Lancement nouveau produit"},
    "gadget":             {"Block Notes", "Calendrier", "Stylo"},
    "specialite_medecin": {
        "Allergologie", "Cardiologie", "Dermatologie", "Endocrinologie",
        "Gastro-entérologie", "Gynécologie", "Médecine générale", "Neurologie",
        "ORL", "Oncologie", "Pneumologie", "Psychiatrie", "Rhumatologie", "Urologie",
    },
}

ALLOWED_INTEREST = {1, 2, 3, 4, 5}

VISIT_OBJECTIVE_MAP = {
    "Prospection": "Promouvoir",
    "Suivi":       "Visite de routine",
    "Lancement":   "Lancement nouveau produit",
}

MIN_WORD_COUNTS = {
    "message_cle":        3,
    "reponse":            5,
    "commentaire_visite": 1,
    "prochaine_action":   2,
}

PENALTY = {
    "missing_required": 10,
    "missing_optional":  2,
    "invalid_value":     8,
    "business_rule":    12,
    "contradiction":    15,
    "duplicate":        20,
    "text_too_short":    5,
}

REJECTION_THRESHOLD = 80


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _word_count(text: Any) -> int:
    return 0 if pd.isna(text) else len(str(text).split())


def _is_empty(value: Any) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def _fuzzy_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


# ─────────────────────────────────────────────────────────────────────────────
# CHECK FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def check_completeness(record: Dict[str, Any]) -> List[Dict[str, str]]:
    """Flag every required field that is missing or empty."""
    is_structured = bool(record.get("_is_structured", True))
    alerts: List[Dict[str, str]] = []

    required = REQUIRED_FIELDS if is_structured else REQUIRED_FIELDS_LIGHT
    optional = [] if is_structured else [
        f for f in REQUIRED_FIELDS if f not in REQUIRED_FIELDS_LIGHT
    ]

    for f in required:
        if f not in record or _is_empty(record.get(f)):
            alerts.append({
                "field": f,
                "rule": "missing_required",
                "severity": "ERROR",
                "message": f"Champ obligatoire manquant : '{f}'",
            })

    for f in optional:
        if f not in record or _is_empty(record.get(f)):
            alerts.append({
                "field": f,
                "rule": "missing_optional",
                "severity": "WARNING",
                "message": f"Champ optionnel manquant : '{f}'",
            })

    return alerts


def check_valid_values(record: Dict[str, Any]) -> List[Dict[str, str]]:
    """Flag categorical fields whose value is not in the allowed set."""
    alerts = []
    for field, allowed in VALID_VALUES.items():
        val = record.get(field)
        if _is_empty(val):
            continue
        if val not in allowed:
            alerts.append({
                "field": field, "rule": "invalid_value", "severity": "ERROR",
                "message": f"Valeur invalide pour '{field}': '{val}'"
            })
    level = record.get("niveau_interet")
    if not _is_empty(level):
        try:
            if int(level) not in ALLOWED_INTEREST:
                alerts.append({
                    "field": "niveau_interet", "rule": "invalid_value", "severity": "ERROR",
                    "message": f"niveau_interet doit être entre 1 et 5, reçu '{level}'"
                })
        except Exception:
            alerts.append({
                "field": "niveau_interet", "rule": "invalid_value", "severity": "ERROR",
                "message": f"niveau_interet doit être numérique, reçu '{level}'"
            })
    return alerts


def check_business_rules(record: Dict[str, Any]) -> List[Dict[str, str]]:
    """Enforce cross-field business rules (type_visite ↔ objectif_visite)."""
    alerts = []
    type_v, obj_v = record.get("type_visite"), record.get("objectif_visite")
    if not _is_empty(type_v) and not _is_empty(obj_v):
        expected = VISIT_OBJECTIVE_MAP.get(type_v)
        if expected and obj_v != expected:
            alerts.append({
                "field": "objectif_visite", "rule": "business_rule", "severity": "ERROR",
                "message": f"Incohérence : {type_v} exige objectif '{expected}', reçu '{obj_v}'."
            })
    return alerts


def check_contradictions(record: Dict[str, Any]) -> List[Dict[str, str]]:
    """Detect semantic contradictions between structured and free-text fields."""
    alerts = []
    text = " ".join([
        str(record.get("commentaire_visite", "")),
        str(record.get("objection", "")),
        str(record.get("reponse", "")),
    ]).lower()

    try:
        niveau = int(record.get("niveau_interet")) if not _is_empty(record.get("niveau_interet")) else None
    except Exception:
        niveau = None

    if niveau is not None:
        if ("retissant" in text or "rétissant" in text) and niveau >= 4:
            alerts.append({
                "field": "niveau_interet", "rule": "contradiction", "severity": "ERROR",
                "message": "Le commentaire suggère un médecin réticent mais le niveau d'intérêt est élevé."
            })
        if ("intéressé" in text or "interesse" in text) and niveau <= 2:
            alerts.append({
                "field": "niveau_interet", "rule": "contradiction", "severity": "WARNING",
                "message": "Le commentaire suggère un médecin intéressé mais le niveau d'intérêt est faible."
            })
    return alerts


def check_text_lengths(record: Dict[str, Any]) -> List[Dict[str, str]]:
    """Flag free-text fields below the minimum word count."""
    alerts = []
    for field, min_wc in MIN_WORD_COUNTS.items():
        value = record.get(field)
        if not _is_empty(value) and _word_count(value) < min_wc:
            alerts.append({
                "field": field, "rule": "text_too_short", "severity": "WARNING",
                "message": f"'{field}' est trop court ({_word_count(value)} mots, min {min_wc})."
            })
    return alerts


def check_duplicates(record: Dict[str, Any], history: pd.DataFrame = None) -> List[Dict[str, str]]:
    """Fuzzy-match the new record against existing records in history."""
    if history is None or history.empty:
        return []
    same_doc  = history[history["nom_medecin"].astype(str).str.lower() == str(record.get("nom_medecin", "")).lower()]
    same_prod = same_doc[same_doc["medicament"].astype(str).str.lower() == str(record.get("medicament", "")).lower()]
    for _, row in same_prod.iterrows():
        sim = _fuzzy_similarity(row.get("message_cle", ""), record.get("message_cle", ""))
        if sim >= 0.95:
            return [{
                "field": "message_cle", "rule": "duplicate", "severity": "WARNING",
                "message": f"Note très proche d'une visite existante (similarité {sim:.2f})."
            }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# SCORING & MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def compute_quality_score(alerts: List[Dict[str, str]]) -> int:
    """Start at 100 and subtract penalties. Clamped to [0, 100]."""
    score = 100 - sum(PENALTY.get(a["rule"], 0) for a in alerts)
    return max(0, min(100, score))


def validate_record(record: Dict[str, Any], history: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Run all integrity checks on a single visit record.

    Parameters
    ----------
    record  : dict           — one visit record (field → value)
    history : pd.DataFrame   — existing records for duplicate detection (optional)

    Returns
    -------
    dict with keys: quality_score, alerts, status
    """
    alerts = []
    alerts += check_completeness(record)
    alerts += check_valid_values(record)
    alerts += check_business_rules(record)
    alerts += check_contradictions(record)
    alerts += check_text_lengths(record)
    alerts += check_duplicates(record, history)

    score  = compute_quality_score(alerts)
    status = "PASS" if score >= REJECTION_THRESHOLD else "REJECT"
    return {"quality_score": score, "alerts": alerts, "status": status}
