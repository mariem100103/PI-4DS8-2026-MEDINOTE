# ================================================================
# routers/ocr.py — CRM Médical · FastAPI
# ================================================================

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import io
from services.extraction_service import extract_from_image, extract_from_pdf

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/image")
async def ocr_image(
    file: UploadFile = File(...),
):
    """Extrait le texte d'une image manuscrite via OCR (Groq Llama 4)."""
    content = await file.read()
    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=422, detail="Fichier image invalide.")
    result = extract_from_image(image)
    return result


@router.post("/pdf")
async def ocr_pdf(
    file: UploadFile = File(...),
):
    """Extrait le texte d'un PDF (natif + OCR pour les pages scannées)."""
    content = await file.read()
    text = extract_from_pdf(content)
    if text.startswith("Erreur") or text.startswith("Module"):
        raise HTTPException(status_code=500, detail=text)
    return {"text": text, "length": len(text)}
