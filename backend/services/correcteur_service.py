"""
Service FastAPI — Correcteur Médical
Migration de correcteur.py (Streamlit/CLI) vers un APIRouter FastAPI.
Expose :
  POST /correcteur/text          → corriger un texte brut
  POST /correcteur/audio         → transcrire + corriger un fichier audio
  GET  /correcteur/health        → santé du service
"""

import logging
import json
import re
import time
import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

try:
    from groq import Groq
except ImportError:
    raise ImportError("❌ Groq non installé. Lancez : pip install groq")

# Import du module médicaments (même qu'avant)
# from medicaments import build_whisper_prompt, get_meds_context
# ⚠️  Si medicaments.py n'est pas encore adapté, on utilise des fallbacks ci-dessous.

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

# ── Configuration ──────────────────────────────────────────────
GROQ_API_KEY = "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"

groq_client = Groq(api_key=GROQ_API_KEY)

USE_LOCAL_WHISPER = os.environ.get("USE_LOCAL_WHISPER", "0") == "1"
LOCAL_WHISPER_MODEL = os.environ.get("LOCAL_WHISPER_MODEL", "large-v3")

# ── Schemas Pydantic ──────────────────────────────────────────
class TextInput(BaseModel):
    texte: str

class CorrectionResult(BaseModel):
    texte_original: str
    texte_corrige: str
    corrections_appliquees: list[str]
    standardisations: list[str]
    score_confiance: float
    type_document: str
    temps_ms: float
    modele: str
    version: str
    transcription_whisper: str | None = None

# ── Knowledge Base médicale ────────────────────────────────────
ABREVIATIONS = {
    "HTA": "hypertension artérielle", "DT2": "diabète de type 2",
    "DT1": "diabète de type 1",       "IDM": "infarctus du myocarde",
    "AVC": "accident vasculaire cérébral", "IC": "insuffisance cardiaque",
    "IRC": "insuffisance rénale chronique", "BPCO": "bronchopneumopathie chronique obstructive",
    "EI": "événement indésirable",    "AMM": "autorisation de mise sur le marché",
    "CHU": "centre hospitalier universitaire", "CH": "centre hospitalier",
}

SHORTCUTS = {
    r'\bdr\b': 'Dr', r'\bpr\b': 'Pr', r'\bpdt\b': 'pendant',
    r'\brdv\b': 'rendez-vous', r'\bptt\b': 'patient',
}

SYSTEM_PROMPT = """Tu es un expert en rédaction médicale professionnelle francophone,
spécialisé dans les rapports et notes des délégués médicaux.

Tes responsabilités :
1. CORRIGER toutes les fautes d'orthographe, grammaire et syntaxe en français.
2. STANDARDISER la terminologie médicale française (DCI, abréviations officielles).
3. AMÉLIORER la clarté sans changer le sens clinique.
4. Reformuler certaines choses pour que ça devient plus explicite.
5. Ne JAMAIS inventer des informations absentes du texte original.
6. Ne JAMAIS modifier les dosages ou données cliniques spécifiques.

Réponds UNIQUEMENT en JSON strict, sans texte avant ni après :
{
  "texte_corrige": "...",
  "corrections_effectuees": ["correction 1", "correction 2"],
  "standardisations": ["standardisation 1"],
  "score_confiance": 0.95
}"""

# ── Helpers (identiques à correcteur.py) ─────────────────────
def preprocess(text: str):
    changes = []
    result = re.sub(r'\r\n', '\n', text)
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'[ \t]+', ' ', result).strip()
    result, n = re.subn(r' ,', ',', result)
    if n: changes.append(f"Ponctuation: {n} espaces avant virgule supprimés")
    result, n = re.subn(r' \.', '.', result)
    if n: changes.append(f"Ponctuation: {n} espaces avant point supprimés")
    for pattern, replacement in SHORTCUTS.items():
        result, n = re.subn(pattern, replacement, result, flags=re.IGNORECASE)
        if n: changes.append(f"Abréviation: '{pattern}' → '{replacement}'")
    result = re.sub(
        r'([.!?]\s+)([a-zàâäéèêëîïôöùûü])',
        lambda m: m.group(1) + m.group(2).upper(), result)
    return result, changes


def detect_type(text: str) -> str:
    t = text.lower()
    if sum(["événement indésirable" in t, "pharmacovigilance" in t, "effet indésirable" in t]) >= 1:
        return "RAPPORT D'ÉVÉNEMENT INDÉSIRABLE"
    if sum(["visite" in t, "prescripteur" in t, "médecin" in t, "consultation" in t]) >= 2:
        return "RAPPORT DE VISITE MÉDICALE"
    if sum(["compte rendu" in t, "activité" in t, "couverture" in t]) >= 2:
        return "COMPTE RENDU D'ACTIVITÉ"
    return "DOCUMENT MÉDICAL GÉNÉRAL"


def calculer_score_reel(texte_original, texte_corrige, corrections, standardisations) -> float:
    mots_orig = len(texte_original.split())
    mots_corr = len(texte_corrige.split())
    nb_corrections = len(corrections)
    nb_std = len(standardisations)
    if mots_corr == 0:
        return 0.0
    ratio_longueur = min(mots_corr / max(mots_orig, 1), 1.5)
    score_longueur = 1.0 if 0.8 <= ratio_longueur <= 1.3 else 0.7
    if nb_corrections == 0:   score_corrections = 0.5
    elif nb_corrections <= 5: score_corrections = 0.75
    elif nb_corrections <= 15: score_corrections = 0.90
    else:                     score_corrections = 0.85
    if nb_std == 0:     score_std = 0.60
    elif nb_std <= 2:   score_std = 0.85
    else:               score_std = 0.95
    score = (score_longueur * 0.20 + score_corrections * 0.40 + score_std * 0.40) + 0.10
    return round(min(max(score, 0.30), 0.99), 2)


def _correct_text(text: str) -> dict:
    """Logique de correction — identique à correcteur.py::correct()"""
    start = time.perf_counter()
    texte_orig = text

    # Essaie d'importer le contexte médicaments (optionnel)
    try:
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from medicaments import load_meds, get_meds_context
        from rapidfuzz import process, fuzz

        data = load_meds()
        tous_les_noms = [e["nom"] for e in data["entries"]]
        
        # Extraire les mots du texte (4+ lettres)
        mots_texte = re.findall(r'\b\w{4,}\b', text)
        
        entries_pertinentes = {}
        for mot in mots_texte:
            matches = process.extract(
                mot.upper(),
                [n.upper() for n in tous_les_noms],
                scorer=fuzz.ratio,
                score_cutoff=75,
                limit=3
            )
            for match_nom, score, _ in matches:
                for e in data["entries"]:
                    if e["nom"].upper() == match_nom:
                        entries_pertinentes[e["nom"]] = e

        if entries_pertinentes:
            meds_ctx = json.dumps(list(entries_pertinentes.values()), ensure_ascii=False)
            logger.info(f"✅ Fuzzy RAG : {len(entries_pertinentes)} médicaments similaires trouvés")
        else:
            meds_ctx = get_meds_context(max_entries=100)
            logger.info("ℹ️ Aucun médicament similaire — contexte général utilisé")

    except Exception as e:
        logger.error(f"❌ Erreur médicaments : {e}")
        meds_ctx = "[]"

    text, pre_changes = preprocess(text)
    doc_type = detect_type(text)
    logger.info(f"Type détecté : {doc_type}")

    ab_ref = json.dumps(ABREVIATIONS, ensure_ascii=False, indent=2)
    prompt = f"""--- TYPE DE DOCUMENT ---
{doc_type}

--- ABRÉVIATIONS DE RÉFÉRENCE ---
{ab_ref}

--- BASE MÉDICAMENTS (noms commerciaux + DCI + dosages) ---
{meds_ctx}

--- TEXTE À CORRIGER ---
\"\"\"{text}\"\"\"
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.1,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)
    elapsed = (time.perf_counter() - start) * 1000

    corrections = pre_changes + result.get("corrections_effectuees", [])
    standardisations = result.get("standardisations", [])
    texte_corrige = result.get("texte_corrige", text)
    score = calculer_score_reel(texte_orig, texte_corrige, corrections, standardisations)

    return {
        "texte_original":         texte_orig,
        "texte_corrige":          texte_corrige,
        "corrections_appliquees": corrections,
        "standardisations":       standardisations,
        "score_confiance":        score,
        "type_document":          doc_type,
        "temps_ms":               round(elapsed, 1),
        "modele":                 "llama-3.3-70b via Groq",
        "version":                "Avec prompt + RAG",
    }


def _transcribe_audio(audio_path: str) -> str:
    """Transcription Whisper via Groq — identique à correcteur.py"""
    try:
        from medicaments import build_whisper_prompt
        prompt = build_whisper_prompt()
    except Exception:
        prompt = "Note médicale francophone."

    with open(audio_path, "rb") as f:
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3-turbo", file=f, language="fr",
            prompt=prompt, response_format="text",
        )
    return transcription if isinstance(transcription, str) else transcription.text


# ── Routes FastAPI ─────────────────────────────────────────────

@router.get("/health")
async def health():
    """Santé du service correcteur."""
    return {"status": "ok", "module": "correcteur_medical"}


@router.post("/text", response_model=CorrectionResult)
async def correct_text(payload: TextInput):
    """
    Corriger un texte médical brut.
    Corps JSON : { "texte": "..." }
    """
    if not payload.texte.strip():
        raise HTTPException(status_code=400, detail="Le champ 'texte' est vide.")
    try:
        result = _correct_text(payload.texte)
        return CorrectionResult(**result)
    except Exception as e:
        logger.error(f"Erreur correction texte : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio", response_model=CorrectionResult)
async def correct_audio(file: UploadFile = File(...)):
    """
    Transcrire un fichier audio puis le corriger.
    Formats acceptés : mp3, wav, m4a, ogg, flac, webm
    """
    SUPPORTED = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
    suffix = os.path.splitext(file.filename or "audio.wav")[1].lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Format non supporté : {suffix}")

    audio_bytes = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        transcript = _transcribe_audio(tmp_path)
        result = _correct_text(transcript)
        result["transcription_whisper"] = transcript
        result["modele"] = "whisper-large-v3-turbo (Groq) + llama-3.3-70b via Groq"
        return CorrectionResult(**result)
    except Exception as e:
        logger.error(f"Erreur correction audio : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
