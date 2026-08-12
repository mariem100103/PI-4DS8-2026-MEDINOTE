from typing import Any, Dict, List


FIELD_WEIGHTS = {
    "nom_prospect": 12,
    "date_visite": 10,
    "objectif_visite": 12,
    "produits_presentes": 15,
    "commentaire": 10,
    "opportunites": 8,
    "benchmarking_concurrents": 6,
    "nombre_echantillons": 6,
    "nom_superviseur": 4,
    "nombre_patients_presents": 5,
    "gadget": 4,
    "date_relance": 4,
    "prochaine_etape": 4,
}


def is_filled(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        value = value.strip().lower()
        return value not in [
            "",
            "null",
            "none",
            "non mentionné",
            "non mentionne",
            "inconnu",
            "n/a",
            "-"
        ]

    if isinstance(value, list):
        return len(value) > 0

    if isinstance(value, (int, float)):
        return value > 0

    return True


def score_products(products: List[Dict[str, Any]]) -> int:
    if not products:
        return 0

    product_scores = []

    for product in products:
        fields = [
            product.get("nom"),
            product.get("commentaire"),
            product.get("opportunites"),
            product.get("benchmarking_concurrents"),
            product.get("nombre_echantillons"),
        ]

        filled = sum(1 for field in fields if is_filled(field))
        product_scores.append(round((filled / len(fields)) * 100))

    return round(sum(product_scores) / len(product_scores))


def calculate_report_score(report_json: Dict[str, Any]) -> Dict[str, Any]:
    if not report_json:
        return {
            "score_rapport": 0,
            "qualite_rapport": "non généré",
            "champs_manquants": list(FIELD_WEIGHTS.keys()),
        }

    total_weight = sum(FIELD_WEIGHTS.values())
    obtained = 0
    missing_fields = []

    for field, weight in FIELD_WEIGHTS.items():
        value = report_json.get(field)

        if field == "produits_presentes":
            product_score = score_products(value or [])
            obtained += weight * (product_score / 100)

            if product_score < 50:
                missing_fields.append(field)

        elif is_filled(value):
            obtained += weight

        else:
            missing_fields.append(field)

    score = round((obtained / total_weight) * 100)

    if score >= 85:
        quality = "excellent"
    elif score >= 70:
        quality = "bon"
    elif score >= 50:
        quality = "moyen"
    else:
        quality = "faible"

    return {
        "score_rapport": score,
        "qualite_rapport": quality,
        "champs_manquants": missing_fields,
    }