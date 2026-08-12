"""
services/text_correction.py
===========================
Wrapper around the correcteur_service to produce a structured record
from a raw note. Uses simple label parsing to fill 14 fields.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


REQUIRED_FIELDS = [
    "region",
    "nom_medecin",
    "specialite_medecin",
    "medicament",
    "indication",
    "type_visite",
    "objectif_visite",
    "message_cle",
    "objection",
    "reponse",
    "niveau_interet",
    "prochaine_action",
    "commentaire_visite",
    "gadget",
]

FIELD_PATTERNS = {
    "region": [r"region\s*[:\-]\s*(.+)"],
    "nom_medecin": [r"nom\s+medecin\s*[:\-]\s*(.+)", r"medecin\s*[:\-]\s*(.+)", r"dr\.?\s+([A-Za-zÀ-ÿ'\-\s]+)"],
    "specialite_medecin": [r"specialite\s+medecin\s*[:\-]\s*(.+)", r"specialite\s*[:\-]\s*(.+)"],
    "medicament": [r"medicament\s*[:\-]\s*(.+)", r"produit\s*[:\-]\s*(.+)"],
    "indication": [r"indication\s*[:\-]\s*(.+)"],
    "type_visite": [r"type\s+visite\s*[:\-]\s*(.+)"],
    "objectif_visite": [r"objectif\s+visite\s*[:\-]\s*(.+)", r"objectif\s*[:\-]\s*(.+)"],
    "message_cle": [r"message\s+cle\s*[:\-]\s*(.+)", r"message\s+cl[ée]\s*[:\-]\s*(.+)"],
    "objection": [r"objection\s*[:\-]\s*(.+)"],
    "reponse": [r"reponse\s*[:\-]\s*(.+)", r"r[eé]ponse\s*[:\-]\s*(.+)"],
    "niveau_interet": [r"niveau\s+interet\s*[:\-]\s*(\d+)"],
    "prochaine_action": [r"prochaine\s+action\s*[:\-]\s*(.+)", r"action\s+suivante\s*[:\-]\s*(.+)"],
    "commentaire_visite": [r"commentaire\s+visite\s*[:\-]\s*(.+)", r"commentaire\s*[:\-]\s*(.+)"],
    "gadget": [r"gadget\s*[:\-]\s*(.+)"]
}

_LABEL_HINT_RE = re.compile(
    r"\b(region|nom\s+medecin|specialite|m[ée]dicament|indication|type\s+visite|objectif|message\s+cl[ée]|objection|r[ée]ponse|niveau\s+interet|prochaine\s+action|commentaire|gadget)\b\s*[:\-]",
    re.IGNORECASE,
)

_SPECIALTY_MAP = {
    "cardiologie": "Cardiologie",
    "dermatologie": "Dermatologie",
    "endocrinologie": "Endocrinologie",
    "gastro-enterologie": "Gastro-entérologie",
    "gastroentérologie": "Gastro-entérologie",
    "gastro-entérologie": "Gastro-entérologie",
    "gynecologie": "Gynécologie",
    "gynécologie": "Gynécologie",
    "medecine generale": "Médecine générale",
    "médecine generale": "Médecine générale",
    "médecine générale": "Médecine générale",
    "neurologie": "Neurologie",
    "orl": "ORL",
    "oncologie": "Oncologie",
    "pneumologie": "Pneumologie",
    "psychiatrie": "Psychiatrie",
    "rhumatologie": "Rhumatologie",
    "urologie": "Urologie",
    "allergologie": "Allergologie",
}

_VISIT_TYPE_HINTS = {
    "lancement": "Lancement",
    "nouveau produit": "Lancement",
    "prospection": "Prospection",
    "premiere visite": "Prospection",
    "première visite": "Prospection",
    "suivi": "Suivi",
    "revisite": "Suivi",
    "relance": "Suivi",
    "connaissait deja": "Suivi",
    "connaissait déjà": "Suivi",
}

_VISIT_OBJECTIVE_MAP = {
    "Prospection": "Promouvoir",
    "Suivi": "Visite de routine",
    "Lancement": "Lancement nouveau produit",
}


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().strip(".\n")


def _extract_fields(text: str) -> Dict[str, Any]:
    record: Dict[str, Any] = {k: "" for k in REQUIRED_FIELDS}

    for field, patterns in FIELD_PATTERNS.items():
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                record[field] = _clean_value(match.group(1))
                break

    if record.get("niveau_interet"):
        try:
            record["niveau_interet"] = int(record["niveau_interet"])
        except Exception:
            pass

    return record


def _extract_sentence(text: str, keywords: List[str]) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text)
    for sentence in parts:
        s_lower = sentence.lower()
        if any(k in s_lower for k in keywords):
            return sentence.strip()
    return ""


def _fallback_enrich_from_free_text(record: Dict[str, Any], text: str) -> Dict[str, Any]:
    enriched = dict(record)
    text_clean = re.sub(r"\s+", " ", text).strip()
    text_lower = text_clean.lower()

    # Commentaire de visite = texte complet si vide
    if not enriched.get("commentaire_visite"):
        enriched["commentaire_visite"] = text_clean

    # Nom du medecin
    if not enriched.get("nom_medecin"):
        try:
            from services.extraction_service import extract_doctors
            docs = extract_doctors(text_clean)
            if docs:
                enriched["nom_medecin"] = docs[0]
        except Exception:
            pass

    # Specialite (uniquement si explicitement mentionnee)
    if not enriched.get("specialite_medecin"):
        m = re.search(r"sp[ée]cialiste\s+en\s+([A-Za-zÀ-ÿ\-\s]+)", text_clean, re.IGNORECASE)
        if m:
            spec = m.group(1).strip().lower()
            spec = re.sub(r"\s+", " ", spec)
            enriched["specialite_medecin"] = _SPECIALTY_MAP.get(spec, spec.title())

    # Prochaine action (seulement si explicitement mentionnee)
    if not enriched.get("prochaine_action") and "relance" in text_lower:
        enriched["prochaine_action"] = _extract_sentence(text_clean, ["relance", "rappel", "revoir", "prochaine", "dans", "jours"])

    return enriched


def parse_and_correct_raw_note(raw_note: str) -> Dict[str, Any]:
    """
    Parse a raw note into a structured record using the corrector output.

    Returns dict with keys:
      record, confidence_score, corrections_log, standardisations
    """
    raw_note = str(raw_note or "").strip()
    corrected_text = raw_note
    corrections: List[str] = []
    standardisations: List[str] = []
    confidence = 0.8

    try:
        from services.correcteur_service import _correct_text

        result = _correct_text(raw_note)
        corrected_text = result.get("texte_corrige", raw_note)
        corrections = result.get("corrections_appliquees", [])
        standardisations = result.get("standardisations", [])
        confidence = float(result.get("score_confiance", 0.8))
    except Exception:
        pass

    record = _extract_fields(corrected_text)
    structured = bool(_LABEL_HINT_RE.search(corrected_text))
    if not structured:
        record = _fallback_enrich_from_free_text(record, corrected_text)
    record["_is_structured"] = structured

    return {
        "record": record,
        "confidence_score": int(round(confidence * 100)),
        "corrections_log": corrections,
        "standardisations": standardisations,
    }


def correct_existing_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pass-through placeholder for structured records.
    """
    return {
        "record": dict(record),
        "confidence_score": 100,
        "corrections_log": [],
        "standardisations": [],
    }
