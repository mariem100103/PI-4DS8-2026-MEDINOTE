from pathlib import Path
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATE_PATH = BASE_DIR / "templates" / "rapport_template.xlsx"
XLSX_DIR = BASE_DIR / "storage" / "xlsx"
XLSX_DIR.mkdir(parents=True, exist_ok=True)


def get_merged_anchor(sheet, cell_ref: str) -> str:
    cell = sheet[cell_ref]
    if not isinstance(cell, MergedCell):
        return cell_ref
    for merged_range in sheet.merged_cells.ranges:
        if cell_ref in merged_range:
            return merged_range.coord.split(":")[0]
    return cell_ref


def safe_set_cell(sheet, cell_ref: str, value):
    anchor = get_merged_anchor(sheet, cell_ref)
    sheet[anchor] = value


def safe_join(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value if x)
    return str(value)


def export_report_to_xlsx(report_id: int, report_json: dict) -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template XLSX not found: {TEMPLATE_PATH}")

    workbook = load_workbook(TEMPLATE_PATH)
    sheet = workbook.active

    # ── Header fields (labels in col B, values in col C) ──────────────────────
    safe_set_cell(sheet, "C2", report_json.get("nom_prospect"))
    safe_set_cell(sheet, "C3", report_json.get("date_visite"))
    safe_set_cell(sheet, "C4", report_json.get("objectif_visite"))

    # ── Product table (headers row 6, data starts row 7, up to 6 products) ────
    # Clear ALL product rows first to remove template placeholder text
    for row in range(7, 13):
        for col in "ABCDE":
            sheet[f"{col}{row}"] = None

    products = report_json.get("produits_presentes") or []
    start_row = 7

    for index, product in enumerate(products):
        if index >= 6:  # template only has 6 product rows (7–12)
            break
        row = start_row + index
        safe_set_cell(sheet, f"A{row}", product.get("nom"))
        safe_set_cell(sheet, f"B{row}", product.get("commentaire"))
        safe_set_cell(sheet, f"C{row}", product.get("opportunites"))
        safe_set_cell(sheet, f"D{row}", safe_join(product.get("benchmarking_concurrents")))
        safe_set_cell(sheet, f"E{row}", product.get("nombre_echantillons"))

    # ── Footer row 14: label | value | label | value | label | value ──────────
    # A14 = "Nom Superviseur"  → value in B14
    # C14 = "Nombre de patients présents" → value in D14
    # E14 = "Gadget:"  → value in F14
    safe_set_cell(sheet, "B14", report_json.get("nom_superviseur"))
    safe_set_cell(sheet, "D14", report_json.get("nombre_patients_presents"))
    safe_set_cell(sheet, "F14", report_json.get("gadget"))

    # ── Row 15: Remarque générale (merged B15:F15) ────────────────────────────
    safe_set_cell(sheet, "B15", report_json.get("remarque_generale"))

    # ── Row 17: Date de relance | value | Prochaine étape | value (merged) ────
    # A17 = "Date de relance" → value in B17
    # C17 = "Prochaine étape" → value in D17 (merged D17:F17)
    safe_set_cell(sheet, "B17", report_json.get("date_relance"))
    safe_set_cell(sheet, "D17", report_json.get("prochaine_etape"))

    output_path = XLSX_DIR / f"rapport_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    workbook.save(output_path)

    return str(output_path)