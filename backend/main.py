import json
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.sawsen_service   import router as persona_router
from services.heatmap_service  import router as heatmap_router
from services.followup_service import router as followup_router

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent))

from models.report_db import Report
from models.user import User
from services.db_service import init_db, get_db
from services.report_service import (
    upload_and_extract,
    update_extracted_text,
    format_report,
    update_report_json,
    export_xlsx,
    soft_delete_report
)

from services.correcteur_service import router as correcteur_router
from services.coaching_service import router as coaching_router
from services.chatbot_service import router as chatbot_router

from routers.analyze import router as analyze_router
from routers.ocr import router as ocr_router
from routers.data import router as data_router
from routers.integrity_router import router as integrity_router
from routers.auth_basic import router as auth_router

app = FastAPI(title="ALIA CRM - Report Extraction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(persona_router,  prefix="/persona",  tags=["HCP Persona"])
app.include_router(heatmap_router,  prefix="/heatmap",  tags=["Heat Map"])
app.include_router(followup_router, prefix="/followup", tags=["Follow-up"])

app.include_router(
    correcteur_router,
    prefix="/correcteur",
    tags=["Correcteur Médical"],
)

app.include_router(
    coaching_router,
    prefix="/coaching",
    tags=["Coaching Délégué"],
)

app.include_router(
    chatbot_router,
    prefix="/chatbot",
    tags=["Chatbot"],
)

app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(ocr_router)
app.include_router(data_router)
app.include_router(integrity_router)
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports/upload")
async def upload_report(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        report = await upload_and_extract(file, db)

        return {
            "success": True,
            "report_id": report.id,
            "name": report.name,
            "source_type": report.source_type,
            "extracted_text": report.extracted_text,
            "status": report.status,
            "created_at": str(report.created_at)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/reports/{report_id}/extracted-text")
def edit_extracted_text(report_id: int, body: dict, db: Session = Depends(get_db)):
    try:
        report = update_extracted_text(report_id, body["extracted_text"], db)
        return {"success": True, "report_id": report.id, "extracted_text": report.extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/{report_id}/format")
def format_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    try:
        report = format_report(report_id, db)
        return {
            "success": True,
            "report_id": report.id,
            "data": json.loads(report.report_json),
            "status": report.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/reports/{report_id}")
def update_report(report_id: int, body: dict, db: Session = Depends(get_db)):
    try:
        report = update_report_json(report_id, body["data"], db)
        return {
            "success": True,
            "report_id": report.id,
            "data": json.loads(report.report_json),
            "status": report.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/{report_id}/export-xlsx")
def export_report(report_id: int, db: Session = Depends(get_db)):
    try:
        report = export_xlsx(report_id, db)
        return {
            "success": True,
            "report_id": report.id,
            "xlsx_path": report.xlsx_path,
            "status": report.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).filter(
        Report.deleted == False
    ).order_by(Report.created_at.desc()).all()

    results = []

    for r in reports:
        report_json = json.loads(r.report_json) if r.report_json else {}

        results.append({
            "id": r.id,
            "name": r.name,
            "original_filename": r.original_filename,
            "status": r.status,
            "source_type": r.source_type,
            "created_at": str(r.created_at),
            "updated_at": str(r.updated_at),
            "xlsx_path": r.xlsx_path,
            "score_rapport": report_json.get("score_rapport", 0),
            "qualite_rapport": report_json.get("qualite_rapport", "non généré"),
            "champs_manquants": report_json.get("champs_manquants", []),
        })

    return results
@app.get("/")
async def root():
    return {"message": "ALIA CRM API is running ✅"}
@app.get("/reports/deleted")
def list_deleted_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.deleted == True).order_by(Report.deleted_at.desc()).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "original_filename": r.original_filename,
            "deleted_at": str(r.deleted_at),
            "delete_reason": r.delete_reason,
            "created_at": str(r.created_at)
        }
        for r in reports
    ]


@app.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report.id,
        "name": report.name,
        "original_filename": report.original_filename,
        "source_type": report.source_type,
        "extracted_text": report.extracted_text,
        "report_json": json.loads(report.report_json) if report.report_json else None,
        "xlsx_path": report.xlsx_path,
        "status": report.status,
        "deleted": report.deleted,
        "created_at": str(report.created_at),
        "updated_at": str(report.updated_at)
    }


@app.get("/reports/{report_id}/download-xlsx")
def download_xlsx(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id, Report.deleted == False).first()

    if not report or not report.xlsx_path:
        raise HTTPException(status_code=404, detail="XLSX not found")

    return FileResponse(
        report.xlsx_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{report.name}.xlsx"
    )


@app.delete("/reports/{report_id}")
def delete_report(report_id: int, reason: str = Form("Deleted by user"), db: Session = Depends(get_db)):
    try:
        report = soft_delete_report(report_id, reason, db)
        return {
            "success": True,
            "report_id": report.id,
            "deleted": report.deleted,
            "deleted_at": str(report.deleted_at),
            "delete_reason": report.delete_reason
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

