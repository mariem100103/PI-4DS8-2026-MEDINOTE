import json
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from services.score_service import calculate_report_score
from models.report_db import Report
from services.extraction_service import extract_pdf_text, pdf_to_images, load_image
from services.groq_service import read_image_with_groq, format_text_to_report_json
from services.xlsx_service import export_report_to_xlsx

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MIN_TEXT_CHARS = 150
MAX_PDF_PAGES = 10


async def save_upload_file(file: UploadFile) -> Path:
    file_path = UPLOAD_DIR / file.filename

    content = await file.read()
    file_path.write_bytes(content)

    return file_path


async def upload_and_extract(file: UploadFile, db):
    file_path = await save_upload_file(file)
    suffix = file_path.suffix.lower()

    source_type = None

    if suffix == ".pdf":
        text = extract_pdf_text(file_path)

        if len(text) >= MIN_TEXT_CHARS:
            source_type = "pdf_text"
        else:
            source_type = "scanned_pdf"
            images = pdf_to_images(file_path, max_pages=MAX_PDF_PAGES)
            page_texts = []

            for i, image in enumerate(images, start=1):
                page_texts.append(f"--- PAGE {i} ---\n{read_image_with_groq(image)}")

            text = "\n\n".join(page_texts)

    elif suffix in [".png", ".jpg", ".jpeg"]:
        source_type = "image"
        image = load_image(file_path)
        text = read_image_with_groq(image)

    else:
        raise ValueError("Format non supporté. Utilise PDF, PNG, JPG ou JPEG.")

    report = Report(
        name=file_path.stem,
        original_filename=file.filename,
        source_type=source_type,
        extracted_text=text,
        status="text_extracted"
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


def update_extracted_text(report_id: int, extracted_text: str, db):
    report = db.query(Report).filter(Report.id == report_id, Report.deleted == False).first()

    if not report:
        raise ValueError("Report not found")

    report.extracted_text = extracted_text
    report.status = "text_modified"
    db.commit()
    db.refresh(report)

    return report


def format_report(report_id: int, db):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.deleted == False
    ).first()

    if not report:
        raise ValueError("Report not found")

    data = format_text_to_report_json(report.extracted_text)

    score_info = calculate_report_score(data)

    data["score_rapport"] = score_info["score_rapport"]
    data["qualite_rapport"] = score_info["qualite_rapport"]
    data["champs_manquants"] = score_info["champs_manquants"]

    report.report_json = json.dumps(data, ensure_ascii=False)
    report.status = "formatted"

    db.commit()
    db.refresh(report)

    return report
def update_report_json(report_id: int, data: dict, db):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.deleted == False
    ).first()

    if not report:
        raise ValueError("Report not found")

    score_info = calculate_report_score(data)

    data["score_rapport"] = score_info["score_rapport"]
    data["qualite_rapport"] = score_info["qualite_rapport"]
    data["champs_manquants"] = score_info["champs_manquants"]

    report.report_json = json.dumps(data, ensure_ascii=False)
    report.status = "modified"

    db.commit()
    db.refresh(report)

    return report

def export_xlsx(report_id: int, db):
    report = db.query(Report).filter(Report.id == report_id, Report.deleted == False).first()

    if not report:
        raise ValueError("Report not found")

    data = json.loads(report.report_json)
    xlsx_path = export_report_to_xlsx(report.id, data)

    report.xlsx_path = xlsx_path
    report.status = "exported"

    db.commit()
    db.refresh(report)

    return report


def soft_delete_report(report_id: int, reason: str, db):
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise ValueError("Report not found")

    report.deleted = True
    report.deleted_at = datetime.now()
    report.delete_reason = reason
    report.status = "deleted"

    db.commit()
    db.refresh(report)

    return report