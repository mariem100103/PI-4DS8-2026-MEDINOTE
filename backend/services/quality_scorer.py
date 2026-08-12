"""
quality_scorer.py
=================
Task 6 — Report Quality Score (0–100)
Medinote | AI-Powered CRM for Medical Representatives

Combines integrity score (Task 5) + confidence score (Task 4)
+ a content richness score into a single composite quality metric.

Quality Score breakdown:
  - Integrity score  (Task 5) : 50% weight — completeness, business rules, contradictions
  - Confidence score (Task 4) : 30% weight — how much correction the text needed
  - Richness score   (new)    : 20% weight — depth and detail of free-text fields

Output:
  quality_score  : int   (0–100)
  grade          : str   ('A', 'B', 'C', 'D', 'F')
  breakdown      : dict  (each component score)
  recommendations: list  (actionable tips to improve the score)
"""

from typing import Any, Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHTS
# ─────────────────────────────────────────────────────────────────────────────

WEIGHT_INTEGRITY   = 0.50
WEIGHT_CONFIDENCE  = 0.30
WEIGHT_RICHNESS    = 0.20

# Minimum word counts considered "rich"
RICH_WORD_TARGETS = {
    "message_cle":        8,
    "reponse":           12,
    "commentaire_visite": 4,
    "prochaine_action":   4,
}

GRADE_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (45, "D"),
    (0,  "F"),
]


# ─────────────────────────────────────────────────────────────────────────────
# RICHNESS SCORE
# ─────────────────────────────────────────────────────────────────────────────

def _compute_richness_score(record: Dict[str, Any]) -> int:
    """
    Score 0–100 measuring how detailed the free-text fields are.
    Each field contributes proportionally to its word count vs target.
    """
    total_weight  = len(RICH_WORD_TARGETS)
    total_earned  = 0.0

    for field, target in RICH_WORD_TARGETS.items():
        val = record.get(field, "")
        if not val or str(val).strip() == "":
            earned = 0.0
        else:
            wc     = len(str(val).split())
            earned = min(1.0, wc / target)
        total_earned += earned

    return int(round((total_earned / total_weight) * 100))


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_recommendations(
    integrity_score: int,
    confidence_score: int,
    richness_score: int,
    alerts: List[Dict],
    record: Dict[str, Any],
) -> List[str]:
    """Generate actionable tips based on what is dragging the score down."""
    tips = []

    # Integrity issues
    error_alerts   = [a for a in alerts if a.get("severity") == "ERROR"]
    warning_alerts = [a for a in alerts if a.get("severity") == "WARNING"]

    if error_alerts:
        fields = [a["field"] for a in error_alerts[:3]]
        tips.append(f"Corrigez les erreurs bloquantes sur : {', '.join(fields)}.")

    if warning_alerts:
        tips.append("Résolvez les avertissements pour améliorer la cohérence de la note.")

    # Confidence issues
    if confidence_score < 70:
        tips.append(
            "Le texte contenait beaucoup de corrections — essayez d'écrire en français "
            "standard dès la saisie pour un score de confiance plus élevé."
        )
    elif confidence_score < 90:
        tips.append("Réduisez les abréviations et fautes d'orthographe médicales.")

    # Richness issues
    for field, target in RICH_WORD_TARGETS.items():
        val = record.get(field, "")
        wc  = len(str(val).split()) if val and str(val).strip() else 0
        if wc < target:
            tips.append(
                f"'{field}' est trop court ({wc} mots). "
                f"Visez au moins {target} mots pour un rapport de qualité."
            )

    if not tips:
        tips.append("Excellent — cette note est complète, cohérente et bien rédigée.")

    return tips


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def compute_report_quality_score(
    record: Dict[str, Any],
    integrity_score: int,
    confidence_score: int,
    alerts: List[Dict],
) -> Dict[str, Any]:
    """
    Compute the composite Report Quality Score (Task 6).

    Parameters
    ----------
    record           : dict  — corrected visit record
    integrity_score  : int   — from Task 5 validate_record()
    confidence_score : int   — from Task 4 correct_*()
    alerts           : list  — from Task 5 validate_record()

    Returns
    -------
    dict with keys:
        quality_score    : int   (0–100)
        grade            : str   ('A'–'F')
        breakdown        : dict  (integrity, confidence, richness component scores)
        recommendations  : list  of str
    """
    richness_score = _compute_richness_score(record)

    quality_score = int(round(
        integrity_score  * WEIGHT_INTEGRITY
        + confidence_score * WEIGHT_CONFIDENCE
        + richness_score   * WEIGHT_RICHNESS
    ))
    quality_score = max(0, min(100, quality_score))

    grade = next(g for threshold, g in GRADE_THRESHOLDS if quality_score >= threshold)

    recommendations = _generate_recommendations(
        integrity_score, confidence_score, richness_score, alerts, record
    )

    return {
        "quality_score":   quality_score,
        "grade":           grade,
        "breakdown": {
            "integrity_score":   integrity_score,
            "confidence_score":  confidence_score,
            "richness_score":    richness_score,
        },
        "recommendations": recommendations,
    }
