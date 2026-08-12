# ================================================================
# extraction_service.py — CRM Médical · FastAPI backend
# AMÉLIORATION : extraction médicaments basée sur le dataset
#   → embedding sémantique + fuzzy matching sur medicaments_final.xlsx
#   → regex en complément secondaire uniquement
# ================================================================
from pathlib import Path
import pdfplumber
import fitz
from PIL import Image

import io, os, re, json, time, hashlib, base64
from difflib import get_close_matches, SequenceMatcher
import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
from PIL import Image
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel, pipeline
from keybert import KeyBERT
import spacy
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
import requests
from functools import lru_cache
from dotenv import load_dotenv

try:
    import fitz
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

# ================================================================
# ⚙️  CONFIGURATION
# ================================================================

BASE_DIR   = Path(__file__).parent.parent
CACHE_DIR  = BASE_DIR / "cache"
HF_CACHE   = BASE_DIR / "hf_cache"
MODELS_DIR = BASE_DIR / "models"

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR.parent / "env")

CACHE_DIR.mkdir(exist_ok=True)
HF_CACHE.mkdir(exist_ok=True)

os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE)
os.environ["HF_HOME"]            = str(HF_CACHE)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
FAST_ANALYSIS = os.getenv("FAST_ANALYSIS", "1").strip().lower() not in {"0", "false", "no"}

CLF_EFFECTS_PATH    = CACHE_DIR / "clf_effects.joblib"
CLF_DRUGS_PATH      = CACHE_DIR / "clf_drugs.joblib"
EMBEDDINGS_PATH     = CACHE_DIR / "drug_embeddings.npy"
DRUG_LIST_PATH      = CACHE_DIR / "drug_list.json"
TRAIN_META_PATH     = CACHE_DIR / "train_meta.json"
DATASET_VOCAB_PATH  = CACHE_DIR / "dataset_vocab.json"

# ── Nouveaux fichiers cache pour l'index médicaments ──────────────
DRUG_INDEX_EMB_PATH  = CACHE_DIR / "drug_index_embeddings.npy"   # embeddings de tous les noms
DRUG_INDEX_LIST_PATH = CACHE_DIR / "drug_index_list.json"        # liste canonique

# ================================================================
# 📊  DATASET
# ================================================================

_df_cache      = None
_df_meds_cache = None

def load_data():
    global _df_cache, _df_meds_cache
    if _df_cache is not None and _df_meds_cache is not None:
        return _df_cache, _df_meds_cache
    try:
        notes_candidates = sorted(MODELS_DIR.glob("data_notes_final_fusione*.xlsx"))
        notes_path = notes_candidates[0] if notes_candidates else (MODELS_DIR / "data_notes_final_fusione.xlsx")
        df = pd.read_excel(notes_path)
        df["full_text"] = (
            df.get("benefitsReview",    pd.Series(dtype=str)).fillna("") + " " +
            df.get("sideEffectsReview", pd.Series(dtype=str)).fillna("") + " " +
            df.get("commentsReview",    pd.Series(dtype=str)).fillna("")
        )
        _df_cache = df[df["full_text"].astype(str).str.strip().ne("")].copy()
    except Exception as e:
        print(f"Erreur chargement notes dataset: {e}")
        _df_cache = pd.DataFrame()
    try:
        _df_meds_cache = pd.read_excel(MODELS_DIR / "medicaments_final.xlsx")
    except Exception as e:
        print(f"Erreur chargement médicaments dataset: {e}")
        _df_meds_cache = pd.DataFrame()
    return _df_cache, _df_meds_cache

# ================================================================
# 💊  INDEX MÉDICAMENTS — construit depuis medicaments_final.xlsx
# ================================================================

_drug_index_cache: dict | None = None


def _load_all_drug_names(df_meds: pd.DataFrame) -> list[str]:
    """
    Extrait tous les noms de médicaments du dataset medicaments_final.xlsx.
    Cherche automatiquement les colonnes pertinentes : nom, nom_commercial,
    dci, substance, molecule, brand_name, drug_name, medicament, etc.
    Retourne une liste dédupliquée de chaînes non vides (≥ 3 caractères).
    """
    name_cols = []
    priority_keywords = ["nom", "name", "dci", "substance", "molecule",
                         "brand", "drug", "medicament", "médicament",
                         "commercial", "générique", "generique"]
    for col in df_meds.columns:
        col_l = col.lower().replace("_", "").replace(" ", "")
        if any(kw in col_l for kw in priority_keywords):
            name_cols.append(col)

    # Si rien trouvé, on prend toutes les colonnes de type object/string
    if not name_cols:
        name_cols = [c for c in df_meds.columns if df_meds[c].dtype == object]

    all_names: set[str] = set()
    for col in name_cols:
        for raw in df_meds[col].dropna().astype(str).unique():
            cleaned = raw.strip()
            if len(cleaned) >= 3 and not cleaned.isdigit():
                all_names.add(cleaned)

    return sorted(all_names)


def build_drug_index(df_meds: pd.DataFrame | None = None) -> dict:
    """
    Construit (ou charge depuis le cache) l'index sémantique des médicaments.
    Retourne :
        {
          "names":      [str, ...],          # noms canoniques
          "names_lower":{str, ...},          # ensemble minuscule
          "embeddings": np.ndarray (N, dim), # vecteurs normalisés
        }
    """
    global _drug_index_cache
    if _drug_index_cache is not None:
        return _drug_index_cache

    # ── Charger depuis le cache disque si dispo ───────────────────
    if DRUG_INDEX_EMB_PATH.exists() and DRUG_INDEX_LIST_PATH.exists():
        names = json.loads(DRUG_INDEX_LIST_PATH.read_text(encoding="utf-8"))
        embs  = np.load(str(DRUG_INDEX_EMB_PATH))
        _drug_index_cache = {
            "names":       names,
            "names_lower": {n.lower() for n in names},
            "embeddings":  embs,
        }
        return _drug_index_cache

    # ── Construire l'index depuis le dataset ──────────────────────
    if df_meds is None or df_meds.empty:
        _, df_meds = load_data()

    names = _load_all_drug_names(df_meds) if df_meds is not None and not df_meds.empty else []

    # Ajouter les médicaments connus en dur comme filet de sécurité
    names = list({*names, *[d.capitalize() for d in KNOWN_DRUGS_FIXED]})
    names = sorted(names)

    print(f"[drug_index] Encodage de {len(names)} médicaments…")
    embedder = get_embedder()
    raw_embs = embedder.encode(names, batch_size=128, show_progress_bar=False,
                               convert_to_numpy=True)
    # Normalisation L2 pour cosinus rapide via simple produit scalaire
    norms    = np.linalg.norm(raw_embs, axis=1, keepdims=True) + 1e-9
    embs     = raw_embs / norms

    DRUG_INDEX_LIST_PATH.write_text(
        json.dumps(names, ensure_ascii=False), encoding="utf-8"
    )
    np.save(str(DRUG_INDEX_EMB_PATH), embs)

    _drug_index_cache = {
        "names":       names,
        "names_lower": {n.lower() for n in names},
        "embeddings":  embs,
    }
    return _drug_index_cache


def invalidate_drug_index():
    """Vide le cache mémoire et disque de l'index médicaments."""
    global _drug_index_cache
    _drug_index_cache = None
    for p in (DRUG_INDEX_EMB_PATH, DRUG_INDEX_LIST_PATH):
        if p.exists():
            p.unlink()

# ================================================================
# 🧠  MODÈLES (chargés une seule fois)
# ================================================================

_embedder          = None
_spacy_model       = None
_kw_model          = None
_sentiment_model   = None
_zeroshot_model    = None
_ner_model         = None
_mbert_tokenizer   = None
_mbert_model       = None
_distilbert_tokenizer = None
_distilbert_model  = None


def _resolve_groq_api_key(api_key: str = "") -> str:
    return (api_key or os.getenv("GROQ_API_KEY") or "").strip()

def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2",
            cache_folder=str(HF_CACHE)
        )
    return _embedder

def get_spacy():
    global _spacy_model
    if _spacy_model is None:
        try:
            _spacy_model = spacy.load("fr_core_news_sm")
        except OSError:
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "fr_core_news_sm"], check=True)
                _spacy_model = spacy.load("fr_core_news_sm")
            except Exception:
                _spacy_model = None
    return _spacy_model

def get_kw() -> KeyBERT:
    global _kw_model
    if _kw_model is None:
        _kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
    return _kw_model

def get_sentiment_model():
    global _sentiment_model
    if _sentiment_model is None:
        _sentiment_model = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            device=0 if DEVICE == "cuda" else -1,
        )
    return _sentiment_model

def get_zeroshot_model():
    global _zeroshot_model
    if _zeroshot_model is None:
        _zeroshot_model = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if DEVICE == "cuda" else -1,
        )
    return _zeroshot_model

def get_ner_model():
    global _ner_model
    if _ner_model is None:
        try:
            _ner_model = pipeline(
                "ner",
                model="Jean-Baptiste/camembert-ner",
                device=0 if DEVICE == "cuda" else -1,
                aggregation_strategy="simple",
            )
        except Exception:
            _ner_model = None
    return _ner_model


def _get_mbert():
    global _mbert_tokenizer, _mbert_model
    if _mbert_model is None or _mbert_tokenizer is None:
        _mbert_tokenizer = AutoTokenizer.from_pretrained(
            "bert-base-multilingual-cased", cache_dir=str(HF_CACHE))
        _mbert_model = AutoModel.from_pretrained(
            "bert-base-multilingual-cased", cache_dir=str(HF_CACHE))
        _mbert_model.eval()
        _mbert_model.to(DEVICE if DEVICE == "cuda" else "cpu")
    return _mbert_tokenizer, _mbert_model


def _get_distilbert():
    global _distilbert_tokenizer, _distilbert_model
    if _distilbert_model is None or _distilbert_tokenizer is None:
        _distilbert_tokenizer = AutoTokenizer.from_pretrained(
            "distilbert-base-multilingual-cased", cache_dir=str(HF_CACHE))
        _distilbert_model = AutoModel.from_pretrained(
            "distilbert-base-multilingual-cased", cache_dir=str(HF_CACHE))
        _distilbert_model.eval()
        _distilbert_model.to(DEVICE if DEVICE == "cuda" else "cpu")
    return _distilbert_tokenizer, _distilbert_model


def _encode_transformer_texts(texts: list, tokenizer, model,
                               max_length: int = 128) -> np.ndarray:
    if not texts:
        return np.empty((0, 1))
    inputs = tokenizer(texts, padding=True, truncation=True,
                       max_length=max_length, return_tensors="pt")
    run_device = DEVICE if DEVICE == "cuda" else "cpu"
    inputs = {k: v.to(run_device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
        last_hidden = outputs.last_hidden_state
        mask = inputs["attention_mask"].unsqueeze(-1).expand(last_hidden.size()).float()
        pooled = (last_hidden * mask).sum(dim=1) / torch.clamp(mask.sum(dim=1), min=1e-9)
    return pooled.detach().cpu().numpy()

# ================================================================
# 🖼️  OCR — GROQ API
# ================================================================

def _img_to_base64_jpeg(image: Image.Image) -> str:
    buf = io.BytesIO()
    img = image.copy()
    if max(img.width, img.height) > 800:
        r = 800 / max(img.width, img.height)
        img = img.resize((int(img.width * r), int(img.height * r)), Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def ocr_groq(image: Image.Image, api_key: str) -> tuple:
    key = _resolve_groq_api_key(api_key)
    if not key:
        return "", 0.0, "Clé API Groq manquante (.env)"
    try:
        img_b64 = _img_to_base64_jpeg(image)
        prompt = (
            "Tu es un système OCR spécialisé en écriture manuscrite française médicale.\n"
            "Transcris mot pour mot le texte manuscrit visible dans cette image.\n"
            "RÈGLES :\n"
            "- Restitue EXACTEMENT chaque mot\n"
            "- Ne corrige pas les noms de médicaments\n"
            "- Si une lettre est ambiguë, garde la forme la plus proche de l'écriture\n"
            "- Retourne UNIQUEMENT le texte transcrit, sans commentaire"
        )
        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]}],
            "max_tokens": 1024,
            "temperature": 0,
        }
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json=payload, timeout=60,
        )
        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"].strip()
            if text:
                words = text.split()
                conf  = min(0.95, len([w for w in words if len(w) > 2]) / max(len(words), 1))
                return text, conf, "Groq (Llama 4 Scout)"
            return "", 0.0, "Aucun texte détecté"
        return "", 0.0, f"Erreur API : {resp.text[:120]}"
    except requests.exceptions.Timeout:
        return "", 0.0, "Timeout — image trop grande"
    except Exception as e:
        return "", 0.0, f"Erreur : {str(e)[:100]}"


def extract_from_image(image: Image.Image, api_key: str = "") -> dict:
    text, conf, engine = ocr_groq(image, api_key)
    return {"text": text, "raw": text, "confidence": conf, "engine": engine}


def extract_from_pdf(pdf_bytes: bytes, api_key: str = "") -> str:
    if not PYMUPDF_OK:
        return "Module pymupdf non installé"
    pages = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            native = page.get_text("text").strip()
            if len(native) > 50:
                pages.append(f"--- Page {i+1} ---\n{native}")
            else:
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                r   = extract_from_image(img, api_key)
                if r["text"]:
                    pages.append(f"--- Page {i+1} (OCR) ---\n{r['text']}")
    return "\n\n".join(pages)

# ================================================================
# 🏋️  ENTRAÎNEMENT
# ================================================================

KNOWN_DRUGS_FIXED = {
    "doliprane", "paracétamol", "paracetamol", "ibuprofène", "ibuprofen",
    "advil", "aspirine", "amoxicilline", "neuropax", "xanax", "valium",
    "morphine", "metformine", "insuline", "ventoline", "cortisone",
    "codéine", "cardiovex", "cardiovéx", "cardiovax", "neurontin",
    "gabapentine", "lyrica", "prégabaline", "oméprazole", "kardégic",
    "amlodipine", "lisinopril", "atorvastatine", "bisoprolol",
}

STOPWORDS_MED = {
    "le", "la", "un", "une", "ce", "cette", "ces", "les", "des", "du",
    "patient", "médecin", "docteur", "docteure", "consultation",
    "traitement", "ordonnance", "dose", "posologie",
    "bilan", "séance", "visite", "résultat",
    "suivi", "tolérance", "discussion", "présence", "utilisation",
    "patients", "patientes", "chroniques", "cas", "progressive",
    "semaines", "certains", "globale", "correcte",
    "actuel", "actuelle", "actuels", "actuelles", "actuellement",
    "temps", "praticien", "praticienne", "praticiens",
    "régulière", "régulier", "régulières", "réguliers",
    "commercial", "commerciaux",
    "délégué", "déléguée", "délégués", "échantillon", "échantillons",
    "informations", "documentation", "brochures", "multicentrique",
}

SIDE_EFFECTS_DICT = {
    "fatigue":       ["fatigue", "fatigué", "fatiguée", "épuisement", "asthénie"],
    "vertiges":      ["vertige", "vertiges", "étourdissement"],
    "douleur":       ["douleur", "douleurs"],
    "nausée":        ["nausée", "nausées", "vomissement", "mal au cœur"],
    "maux de tête":  ["maux de tête", "céphalée", "céphalées", "migraine"],
    "insomnie":      ["insomnie", "difficulté à dormir", "sommeil perturbé"],
    "somnolence":    ["somnolence", "endormissement", "somnolent"],
    "palpitations":  ["palpitation", "palpitations", "tachycardie"],
    "éruption":      ["éruption", "rash", "urticaire", "démangeaison"],
    "constipation":  ["constipation"],
    "diarrhée":      ["diarrhée"],
    "anxiété":       ["anxiété", "anxieux", "angoisse"],
}

NEGATION_CTX = {
    "amélioration", "diminution", "moins", "disparition",
    "réduit", "résolu", "sans", "pas de", "absence",
}

VISIT_LABELS = [
    "Consultation de suivi",
    "Prescription médicamenteuse",
    "Rapport de visite (délégué médical)",
    "Effets secondaires",
    "Efficacité thérapeutique",
    "Consultation initiale",
    "Urgence médicale",
    "Bilan de santé",
]

# Patterns regex gardés UNIQUEMENT comme filet de sécurité secondaire
DRUG_PATTERNS = [
    r"(?i)traitement(?:\s+par)?\s+([A-Za-zÀ-ÿ]{4,})",
    r"(?i)([A-Za-zÀ-ÿ]{4,})\s+(?:prescrit|prescrits|ajouté|administré|pris|initié|commencé)",
    r"(?i)(?:prescription|posologie)\s+(?:de\s+)?([A-Za-zÀ-ÿ]{4,})",
    r"(?i)(?:sous|avec)\s+(?:le\s+|un\s+|une\s+)?([A-Za-zÀ-ÿ]{4,})(?:\s+\d+\s*(?:mg|ml|g|µg))?",
    r"(?i)(?:concernant|indiqué|utilisation\s+de)\s+([A-Za-zÀ-ÿ]{4,})",
    r"([A-Za-zÀ-ÿ]{4,})\s+\d+\s*(?:mg|ml|g|µg|mcg|UI)\b",
    r"([A-Za-zÀ-ÿ]{4,})\d+\s*(?:mg|ml|g|µg|mcg|UI)?\b",
]


def _dataset_hash(df: pd.DataFrame) -> str:
    return hashlib.md5(f"{len(df)}_{list(df.columns)}".encode()).hexdigest()[:12]


def needs_training(df: pd.DataFrame) -> bool:
    if not TRAIN_META_PATH.exists():
        return True
    return json.loads(TRAIN_META_PATH.read_text()).get("hash") != _dataset_hash(df)


def train_and_save(df: pd.DataFrame) -> dict:
    emb    = get_embedder()
    report = {}

    side_col   = next((c for c in df.columns if "sideeffect" in c.lower() or "side" in c.lower()), None)
    rating_col = next((c for c in df.columns if "rating" in c.lower()), None)
    if side_col and rating_col:
        df_eff = df[[side_col, rating_col]].dropna().copy()
        if len(df_eff) >= 20:
            def _lbl(v):
                try:
                    v = float(v)
                    return "positif" if v >= 4 else "négatif" if v <= 2 else "neutre"
                except Exception:
                    return None
            df_eff["lbl"] = df_eff[rating_col].apply(_lbl)
            df_eff = df_eff.dropna(subset=["lbl"])
            X_eff  = emb.encode(df_eff[side_col].tolist(), batch_size=64, show_progress_bar=False)
            le_eff = LabelEncoder()
            y_eff  = le_eff.fit_transform(df_eff["lbl"].tolist())
            clf_eff = LogisticRegression(max_iter=1000, C=1.0)
            clf_eff.fit(X_eff, y_eff)
            scores = cross_val_score(clf_eff, X_eff, y_eff, cv=3, scoring="f1_macro")
            report["effects_f1"] = round(float(scores.mean()), 3)
            joblib.dump({"clf": clf_eff, "le": le_eff}, CLF_EFFECTS_PATH)

    drug_col = next(
        (c for c in df.columns if "drug" in c.lower() or "médicament" in c.lower()), None
    )
    dataset_drugs: list = []
    if drug_col and df[drug_col].notna().sum() >= 10:
        dataset_drugs = [str(d).strip() for d in df[drug_col].dropna().unique()
                         if len(str(d).strip()) > 2]
        pos  = dataset_drugs[:500]
        neg  = ["patient", "médecin", "traitement", "consultation",
                "douleur", "symptôme", "dose", "bilan", "résultat"]
        X_drug = emb.encode(pos + neg, batch_size=64, show_progress_bar=False)
        clf_drug = LogisticRegression(max_iter=500)
        clf_drug.fit(X_drug, [1] * len(pos) + [0] * len(neg))
        report["drugs_trained"] = len(pos)
        joblib.dump(clf_drug, CLF_DRUGS_PATH)
        drug_list = dataset_drugs[:1000]
        np.save(str(EMBEDDINGS_PATH),
                emb.encode(drug_list, batch_size=64, show_progress_bar=False))
        DRUG_LIST_PATH.write_text(json.dumps(drug_list, ensure_ascii=False))

    vocab: dict = {"drugs": dataset_drugs, "drug_freq": {}, "effects_freq": {}}
    if dataset_drugs:
        all_txt = " ".join(df["full_text"].tolist()).lower()
        for d in dataset_drugs:
            cnt = all_txt.count(d.lower())
            if cnt > 0:
                vocab["drug_freq"][d] = cnt
    if side_col and side_col in df.columns:
        eff_txt = " ".join(df[side_col].dropna().tolist()).lower()
        for eff, variants in SIDE_EFFECTS_DICT.items():
            cnt = sum(eff_txt.count(v) for v in variants)
            if cnt > 0:
                vocab["effects_freq"][eff] = cnt
    DATASET_VOCAB_PATH.write_text(json.dumps(vocab, ensure_ascii=False, indent=2))
    report["vocab_drugs"] = len(vocab["drugs"])

    TRAIN_META_PATH.write_text(json.dumps({
        "hash":      _dataset_hash(df),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "report":    report,
    }, ensure_ascii=False, indent=2))

    # Reconstruire l'index médicaments après entraînement
    invalidate_drug_index()
    _, df_meds = load_data()
    build_drug_index(df_meds)

    return report


_trained_models_cache = None

def load_trained_models() -> dict:
    global _trained_models_cache
    if _trained_models_cache is not None:
        return _trained_models_cache
    m: dict = {
        "clf_eff":             None,
        "le_eff":              None,
        "clf_drug":            None,
        "drug_embs":           None,
        "drug_list":           [],
        "dataset_drugs_lower": set(),
        "effects_freq":        {},
    }
    if CLF_EFFECTS_PATH.exists():
        d = joblib.load(CLF_EFFECTS_PATH)
        m["clf_eff"], m["le_eff"] = d["clf"], d["le"]
    if CLF_DRUGS_PATH.exists():
        m["clf_drug"] = joblib.load(CLF_DRUGS_PATH)
    if EMBEDDINGS_PATH.exists() and DRUG_LIST_PATH.exists():
        m["drug_embs"] = np.load(str(EMBEDDINGS_PATH))
        m["drug_list"] = json.loads(DRUG_LIST_PATH.read_text())
    if DATASET_VOCAB_PATH.exists():
        v = json.loads(DATASET_VOCAB_PATH.read_text())
        m["dataset_drugs_lower"] = {d.lower() for d in v.get("drugs", [])}
        m["effects_freq"]        = v.get("effects_freq", {})
    _trained_models_cache = m
    return m

# ================================================================
# 🔬  EXTRACTION
# ================================================================

def extract_crm_fiche(text: str) -> dict:
    """Extraits pour rapports CRM / visite médicale (délégué) — lignes Étiquette : valeur."""
    tl = text.lower()
    if "médecin visité" not in tl and "médecin visite" not in tl:
        return {}
    if "date de visite" not in tl:
        return {}

    fields: dict = {}

    def one_line(pat: str, key: str):
        m = re.search(pat, text, re.I | re.MULTILINE)
        if m:
            v = re.sub(r"\s+", " ", m.group(1)).strip()
            fields[key] = v

    def paragraph_after(pat: str, key: str, max_chars: int = 900):
        m = re.search(pat, text, re.I | re.MULTILINE)
        if not m:
            return
        rest = text[m.end():].lstrip("\n:")
        if not rest:
            return
        paragraph = rest.split("\n\n", 1)[0].strip()
        paragraph = " ".join(paragraph.splitlines()).strip()
        paragraph = re.sub(r"[ \t]+", " ", paragraph)
        if paragraph:
            if len(paragraph) > max_chars:
                paragraph = paragraph[:max_chars] + "…"
            fields[key] = paragraph

    one_line(r"Date\s+de\s+visite\s*[:\s]+\s*([^\n]+)",    "Date de visite")
    one_line(r"Délégué\s+médical\s*[:\s]+\s*([^\n]+)",     "Délégué médical")
    one_line(r"Zone\s*[:\s]+\s*([^\n]+)",                   "Zone")
    one_line(r"Médecin\s+visité\s*[:\s]+\s*([^\n]+)",      "Médecin visité")
    one_line(r"Sp[eé]cialit[eé]\s*[:\s]+\s*([^\n]+)",     "Spécialité")
    one_line(r"Établissement\s*[:\s]+\s*([^\n]+)",          "Établissement")
    one_line(r"Heure\s+de\s+visite\s*[:\s]+\s*([^\n]+)",  "Heure de visite")
    one_line(r"Dur[eé]e\s*[:\s]+\s*([^\n]+)",             "Durée")
    paragraph_after(r"Objet\s+de\s+la\s+visite\s*[:\s]*", "Objet de la visite")
    paragraph_after(r"Conclusion\s*[:\s]*",                 "Conclusion")

    return {k: v for k, v in fields.items() if v}


def _is_crm_visite_entete(text: str) -> bool:
    tl = text.lower()
    return (
        ("médecin visité" in tl or "médecin visite" in tl)
        and "date de visite" in tl
        and len(re.findall(r"\bDate\s+de\s+visite\b", text, flags=re.I)) < 2
    )


# ================================================================
# 💊  EXTRACTION MÉDICAMENTS — AMÉLIORÉE
# ================================================================

COMMON_WORDS_FILTER = {
    "Après", "Avant", "Aussi", "Bien", "Dans", "Lors", "Mais",
    "Note", "Pour", "Sans", "Très", "Tout", "Voici", "Avec",
    "Chez", "Donc", "Cette", "Suite", "Selon", "Entre", "Discussion",
    "Plusieurs", "Présence", "Poursuite", "Traitement", "Utilisation",
    "Actuel", "Actuelle", "Actuellement", "Temps",
}

# Médicaments dont le nom coïncide avec un mot commun français/anglais.
# Pour ces noms, la présence seule dans le texte ne suffit pas :
# un contexte médical explicite est requis (dosage, verbe médical, etc.).
AMBIGUOUS_DRUG_NAMES: set[str] = {
    "moment", "actron", "avant", "libre", "forte", "simple", "plus",
    "extra", "rapid", "active", "action", "control", "flex", "care",
    "total", "ultra", "mega", "max", "mini", "neo", "prime", "classic",
    "balance", "comfort", "complete", "motion", "relief", "calm",
    "rest", "sleep", "energy", "boost", "vital", "force", "nature",
    "herbal", "pure", "clear", "fresh", "cool", "warm", "smart",
}

# Mots déclencheurs d'un contexte médical dans la fenêtre autour du mot
_MEDICAL_CONTEXT_WORDS = {
    "mg", "ml", "cp", "comprimé", "gélule", "dose", "posologie",
    "prescrit", "prescription", "traitement", "administré", "pris",
    "sous", "avec le", "avec la", "initié", "arrêté", "continuer",
    "ordonnance", "médicament", "thérapie", "indiqué", "ajouté",
}

_WINDOW = 80   # caractères autour du mot pour chercher le contexte


def _has_medical_context(drug_l: str, text_lower: str) -> bool:
    """Vérifie qu'un contexte médical existe dans les ±80 car. autour du drug."""
    pos = text_lower.find(drug_l)
    if pos == -1:
        return False
    ctx = text_lower[max(0, pos - _WINDOW): pos + len(drug_l) + _WINDOW]
    return any(cw in ctx for cw in _MEDICAL_CONTEXT_WORDS)


def _tokenize_text(text: str) -> list[str]:
    """
    Découpe le texte en tokens de ≥ 4 caractères, en ignorant les mots vides.
    Retourne les tokens dans leur casse originale.
    """
    raw_tokens = re.findall(r"[A-Za-zÀ-ÿ\-]{4,}", text)
    stop_lower = STOPWORDS_MED | {w.lower() for w in COMMON_WORDS_FILTER}
    return [t for t in raw_tokens if t.lower() not in stop_lower and not t.isdigit()]


def _drug_present_in_text(drug_name: str, text_lower: str) -> bool:
    """
    Vérifie qu'un nom de médicament est réellement présent dans le texte.

    Niveaux de tolérance (du plus strict au plus souple) :
      1. Correspondance exacte mot entier  → accepté directement
      2. Inclusion : le drug est dans un token OCR (ex: 'ardiovex' contient 'ardiovex')
         ou l'inverse (OCR a ajouté des lettres)
      3. Similarité SequenceMatcher ≥ 0.78 contre tous les tokens ≥ 5 car.
         → gère les troncatures OCR comme 'ardiovex' vs 'cardiovex'

    Pour les noms AMBIGUS (MOMENT, CALM…) : exige en plus un contexte médical.
    Rejette les noms < 5 caractères et les stopwords.
    """
    drug_l = drug_name.strip().lower()
    if len(drug_l) < 5:
        return False
    if drug_l in STOPWORDS_MED:
        return False

    # Noms ambigus → contexte médical obligatoire, peu importe la présence
    if drug_l in AMBIGUOUS_DRUG_NAMES:
        return _has_medical_context(drug_l, text_lower)

    text_tokens = re.findall(r"[a-zà-ÿœ]{5,}", text_lower)

    # Niveau 1 — exact (mot entier)
    if re.search(rf"(?<![a-zà-ÿ]){re.escape(drug_l)}(?![a-zà-ÿ])", text_lower):
        return True

    # Niveau 2 — inclusion (gère ajouts/suppressions de lettres par OCR)
    for tok in text_tokens:
        # Le drug est dans le token (ex: neurontin → neurontine)
        if drug_l in tok:
            return True
        # Le token est dans le drug (OCR a tronqué, ex: ardiovex dans cardiovex)
        if len(tok) >= 5 and tok in drug_l:
            return True

    # Niveau 3 — similarité de chaîne (rattrape les décalages OCR)
    # Seuil abaissé à 0.78 pour attraper 'ardiovex' <-> 'cardiovex' (ratio ≈ 0.80)
    for tok in text_tokens:
        ratio = SequenceMatcher(None, drug_l, tok).ratio()
        if ratio >= 0.78:
            return True

    return False


def _semantic_search_in_index(
    query_tokens: list[str],
    text_lower: str,
    index: dict,
    top_k: int = 15,
    sim_threshold: float = 0.88,  # seuil relevé — évite les faux positifs sémantiques
) -> list[str]:
    """
    Étape 1 — Recherche sémantique :
    • Encode les tokens du texte
    • Calcule la similarité cosinus contre tous les médicaments de l'index
    • Ne retient que ceux dont le score ≥ sim_threshold ET qui sont
      réellement présents dans le texte (validation stricte)
    """
    if not query_tokens or index["embeddings"] is None:
        return []

    embedder = get_embedder()
    tok_vecs = embedder.encode(query_tokens, convert_to_numpy=True, batch_size=64)
    norms    = np.linalg.norm(tok_vecs, axis=1, keepdims=True) + 1e-9
    tok_vecs = tok_vecs / norms

    # sim_matrix : shape (nb_tokens, nb_drugs)
    sim_matrix   = tok_vecs @ index["embeddings"].T
    best_per_drug = sim_matrix.max(axis=0)   # meilleur score parmi tous les tokens pour chaque drug

    top_indices = np.argsort(best_per_drug)[::-1][:top_k]
    results = []
    for idx in top_indices:
        score = float(best_per_drug[idx])
        if score < sim_threshold:
            break
        drug = index["names"][int(idx)]
        # Validation stricte : le médicament doit être présent dans le texte
        if _drug_present_in_text(drug, text_lower):
            results.append(drug)
    return results


def _fuzzy_match_in_index(
    query_tokens: list[str],
    text_lower: str,
    index: dict,
    cutoff: float = 0.88,   # cutoff relevé pour éviter les faux positifs
) -> list[str]:
    """
    Étape 2 — Fuzzy matching token par token :
    • Correspondance exacte ou proche (difflib) dans l'index
    • Double validation : le token ET le drug candidat doivent passer
      _drug_present_in_text pour être retenus
    """
    names_lower = list(index["names_lower"])
    names_map   = {n.lower(): n for n in index["names"]}
    found = set()
    for tok in query_tokens:
        tok_l = tok.lower()
        if len(tok_l) < 5:
            continue
        # Correspondance exacte
        if tok_l in names_map:
            canon = names_map[tok_l]
            if _drug_present_in_text(canon, text_lower):
                found.add(canon)
            continue
        # Fuzzy
        close = get_close_matches(tok_l, names_lower, n=1, cutoff=cutoff)
        if close:
            canon = names_map[close[0]]
            if _drug_present_in_text(canon, text_lower):
                found.add(canon)
    return list(found)


def _regex_candidates_in_index(
    text: str,
    text_lower: str,
    index: dict,
    cutoff: float = 0.86,
) -> list[str]:
    """
    Étape 3 (filet de sécurité) — Regex contextuels :
    • Extrait les candidats via les patterns de contexte médical
    • Les valide dans l'index par correspondance exacte ou fuzzy (cutoff élevé)
    • Ne retourne que les médicaments confirmés présents dans le texte
    """
    names_lower = list(index["names_lower"])
    names_map   = {n.lower(): n for n in index["names"]}
    found = set()
    for pattern in DRUG_PATTERNS:
        for m in re.findall(pattern, text):
            cand = m.strip().split()[0]
            cand_l = cand.lower()
            if len(cand_l) < 5 or cand_l in STOPWORDS_MED:
                continue
            # Exact
            if cand_l in names_map:
                canon = names_map[cand_l]
                if _drug_present_in_text(canon, text_lower):
                    found.add(canon)
                continue
            # Fuzzy
            close = get_close_matches(cand_l, names_lower, n=1, cutoff=cutoff)
            if close:
                canon = names_map[close[0]]
                if _drug_present_in_text(canon, text_lower):
                    found.add(canon)
    return list(found)


def extract_drugs(text: str, models: dict) -> list[str]:
    """
    Extraction des médicaments en 3 étapes ordonnées par priorité.

    Chaque étape exige que le médicament trouvé soit réellement
    présent dans le texte (_drug_present_in_text) — ce garde-fou
    élimine les faux positifs sémantiques comme MOMENT, VALUE, ECOREX.

    1. Sémantique (cosinus ≥ 0.88) + validation présence texte
    2. Fuzzy matching (cutoff 0.88) + validation présence texte
    3. Regex contextuels → fuzzy index (cutoff 0.86) + validation présence texte
    """
    _, df_meds = load_data()
    index      = build_drug_index(df_meds)
    text_lower = text.lower()

    # ── Tokens candidats (longueur ≥ 5, non stopwords) ───────────
    tokens = _tokenize_text(text)
    seen_tok: set  = set()
    unique_tokens  = []
    for t in tokens:
        if len(t) >= 5 and t.lower() not in seen_tok:
            seen_tok.add(t.lower())
            unique_tokens.append(t)

    found: set[str] = set()

    # Etape 1 : semantique (seuil 0.88 + validation presence)
    semantic_hits = _semantic_search_in_index(
        unique_tokens, text_lower, index, top_k=15, sim_threshold=0.88
    )
    found.update(semantic_hits)

    # Etape 2 : fuzzy matching (cutoff 0.88 + validation presence)
    fuzzy_hits = _fuzzy_match_in_index(
        unique_tokens, text_lower, index, cutoff=0.88
    )
    found.update(fuzzy_hits)

    # Etape 3 : regex contextuels (cutoff 0.86 + validation presence)
    regex_hits = _regex_candidates_in_index(
        text, text_lower, index, cutoff=0.86
    )
    found.update(regex_hits)

    # Filtrage final
    stop_lower = STOPWORDS_MED | {w.lower() for w in COMMON_WORDS_FILTER}
    cleaned = [
        d for d in found
        if d.lower() not in stop_lower
        and d not in COMMON_WORDS_FILTER
        and len(d) >= 5
        and _drug_present_in_text(d, text_lower)
    ]

    return sorted(set(cleaned))


# ================================================================
#  (Reste du fichier inchangé)
# ================================================================

def extract_doctors(text: str) -> list:
    raw_names: list = []
    seen_raw:  set  = set()

    def _collect(name: str):
        clean = re.sub(r"\s+", " ", name).strip()
        if (len(clean) < 3
                or clean.lower() in STOPWORDS_MED
                or clean.lower() in KNOWN_DRUGS_FIXED
                or clean.lower() in seen_raw):
            return
        seen_raw.add(clean.lower())
        raw_names.append(clean)

    m_cv = re.search(
        r"Médecin\s+visité\s*[:\t\s]+\s*(?:Dr\.?\s*)?([^\n\r]+)",
        text, re.I
    )
    if m_cv:
        line = re.sub(r"\s+", " ", m_cv.group(1).strip())
        line = line.split("/", 1)[0].strip()
        line = re.split(r"\s+[Ss]p(?:e|é)c", line)[0].strip()
        line = re.split(r"\s+[Éé]tab", line)[0].strip()
        if line.lower().startswith("dr."):
            line = line[3:].strip()
        elif line.lower().startswith("dr "):
            line = line[3:].strip()
        _collect(line)

    for pat in [r"(?:Dr\.?|Docteur[e]?|Pr\.?)\s+([A-ZÀ-Ü][a-zà-ü]+(?:[-\s][A-ZÀ-Ü][a-zà-ü]+){0,2})"]:
        for m in re.findall(pat, text):
            _collect(m.strip())

    if not FAST_ANALYSIS:
        ner = get_ner_model()
        if ner is not None:
            try:
                for ent in ner(text[:512]):
                    if ent.get("entity_group") == "PER" and ent.get("score", 0) > 0.85:
                        _collect(ent["word"])
            except Exception:
                pass

        nlp = get_spacy()
        if nlp is not None:
            try:
                for ent in nlp(text[:1000]).ents:
                    if ent.label_ in ("PER", "PERSON"):
                        _collect(ent.text)
            except Exception:
                pass

    ordered_by_size = sorted(raw_names, key=lambda n: len(n), reverse=True)
    deduplicated: list = []
    raw_lower = [n.lower() for n in ordered_by_size]
    for i, name in enumerate(ordered_by_size):
        name_l = name.lower()
        is_substring = any(
            name_l != other_l and name_l in other_l
            for other_l in raw_lower
        )
        if not is_substring:
            prefix = "Dr. " if not re.match(r"(?i)^(dr|pr|docteur)", name) else ""
            deduplicated.append(prefix + name)

    seen_display: set = set()
    result: list = []
    for d in deduplicated:
        key = d.lower()
        if key not in seen_display:
            seen_display.add(key)
            result.append(d)
    return result


def extract_effects(text: str, models: dict) -> dict:
    text_lower   = text.lower()
    effects: dict = {}
    effects_freq  = models.get("effects_freq", {})
    negated: set = set()

    for eff in sorted(SIDE_EFFECTS_DICT, key=lambda k: effects_freq.get(k, 0), reverse=True):
        if eff in negated:
            continue
        for variant in SIDE_EFFECTS_DICT[eff]:
            pos = text_lower.find(variant)
            if pos == -1:
                continue
            ctx = text_lower[max(0, pos - 50): min(len(text_lower), pos + 60)]
            if any(neg in ctx for neg in NEGATION_CTX):
                continue
            freq  = effects_freq.get(eff, 0)
            label = f"indésirable · fréquent ({freq}×)" if freq > 5 else "indésirable"
            effects[eff] = label
            break

    return effects


def get_sentiment(text: str, models: dict) -> str:
    clf_eff = models.get("clf_eff")
    le_eff  = models.get("le_eff")
    if clf_eff is not None and le_eff is not None:
        try:
            emb   = get_embedder()
            vec   = emb.encode([text[:512]])
            pred  = clf_eff.predict(vec)[0]
            proba = clf_eff.predict_proba(vec)[0].max()
            if proba >= 0.60:
                return le_eff.inverse_transform([pred])[0]
        except Exception:
            pass

    try:
        result = get_sentiment_model()(text[:512])[0]
        label  = result["label"]
        if "4 star" in label or "5 star" in label:
            return "positif"
        if "1 star" in label or "2 star" in label:
            return "négatif"
        return "neutre"
    except Exception:
        pass

    tl = text.lower()
    pos = sum(1 for w in ["amélioration", "efficace", "stable", "bien contrôlé", "satisfait"] if w in tl)
    neg = sum(1 for w in ["fatigue", "vertige", "douleur", "aggravation", "échec", "préoccupé"] if w in tl)
    if pos > neg:
        return "positif"
    if neg > pos:
        return "négatif"
    return "neutre"


def classify_visit(text: str) -> str:
    if _is_crm_visite_entete(text):
        return "Rapport de visite (délégué médical)"
    lemmas: set = set()
    if not FAST_ANALYSIS:
        try:
            result = get_zeroshot_model()(text[:500], VISIT_LABELS)
            if result["scores"][0] > 0.35:
                return result["labels"][0]
        except Exception:
            pass

        nlp = get_spacy()
        if nlp is not None:
            try:
                doc = nlp(text[:500])
                lemmas = {token.lemma_.lower() for token in doc}
            except Exception:
                pass

    tl = text.lower()
    if any(w in tl or w in lemmas for w in ["suivi", "évolution", "contrôle", "contrôler"]):
        return "Consultation de suivi"
    if any(w in tl for w in ["prescrit", "prescription", "posologie", "ordonnance"]):
        return "Prescription médicamenteuse"
    if any(w in tl for w in ["effet secondaire", "indésirable", "tolérance"]):
        return "Effets secondaires"
    if any(w in tl or w in lemmas for w in ["amélioration", "efficace", "améliorer"]):
        return "Efficacité thérapeutique"
    if any(w in tl for w in ["urgence", "hospitalisation"]):
        return "Urgence médicale"
    return "Consultation de suivi"


def _summarize_via_groq(text: str, api_key: str) -> str:
    key = _resolve_groq_api_key(api_key)
    if not key:
        return ""
    prompt = f"""Tu es un assistant médical. Rédige un résumé clinique COURT et CLAIR en français
de la note de visite médicale ci-dessous.

RÈGLES STRICTES :
- Réponse en français UNIQUEMENT
- 3 à 5 phrases maximum
- Mentionner : médicament(s), médecin si cité, effets observés, décision/suivi
- Ton factuel et professionnel
- Interdiction de recopier les phrases de la note
- Ne jamais reprendre plus de 6 mots consécutifs du texte d'origine

NOTE :
{text[:2500]}

Résumé clinique :"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.2,
            },
            timeout=30,
        )
        if r.status_code == 200:
            summary = r.json()["choices"][0]["message"]["content"].strip()
            if len(summary) > 20 and "je ne peux pas" not in summary.lower():
                return summary
    except Exception:
        pass
    return ""


def _summarize_extractive_fr(text: str) -> str:
    try:
        nlp = get_spacy()
        sentences = []
        if nlp is not None:
            doc = nlp(text[:1500])
            sentences = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 20]
        if not sentences:
            sentences = [s.strip() for s in re.split(r"[.!?]\s+", text) if len(s.strip()) > 20]
        if not sentences:
            return text[:300]

        kw_model = get_kw()
        kw_set = {kw for kw, _ in kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), top_n=6)}
        scored = sorted(
            [(sum(1 for kw in kw_set if kw.lower() in s.lower()), s) for s in sentences[:15]],
            key=lambda x: -x[0],
        )
        top = [s for _, s in scored[:3]]
        return " ".join(top) if top else sentences[0]
    except Exception:
        return text[:300] if len(text) > 300 else text


def _summarize_extractive_distilbert(text: str) -> str:
    try:
        nlp = get_spacy()
        sentences = []
        if nlp is not None:
            doc = nlp(text[:2000])
            sentences = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 25]
        if not sentences:
            sentences = [s.strip() for s in re.split(r"[.!?]\s+", text) if len(s.strip()) > 25]
        if not sentences:
            return text[:300] if len(text) > 300 else text

        sentences = sentences[:12]
        tok, mdl  = _get_distilbert()
        sent_vecs = _encode_transformer_texts(sentences, tok, mdl, max_length=128)
        if len(sent_vecs) == 0:
            return _summarize_extractive_fr(text)

        centroid      = sent_vecs.mean(axis=0)
        centroid_norm = np.linalg.norm(centroid) + 1e-9
        scored = []
        for idx, vec in enumerate(sent_vecs):
            score = float(np.dot(vec, centroid) / ((np.linalg.norm(vec) + 1e-9) * centroid_norm))
            scored.append((idx, score, sentences[idx]))
        best    = sorted(scored, key=lambda x: x[1], reverse=True)[:3]
        ordered = [s for _, _, s in sorted(best, key=lambda x: x[0])]
        return " ".join(ordered) if ordered else sentences[0]
    except Exception:
        return _summarize_extractive_fr(text)


def _tokenize_for_overlap(text: str) -> set:
    tokens = re.findall(r"[A-Za-zÀ-ÿ]{3,}", text.lower())
    return set(tokens)


def _is_too_close_to_source(summary: str, source: str) -> bool:
    s   = summary.strip().lower()
    src = source.strip().lower()
    if not s or not src:
        return False
    if s in src:
        return True
    src_tokens = _tokenize_for_overlap(src)
    sum_tokens = _tokenize_for_overlap(s)
    if not sum_tokens:
        return False
    overlap_ratio = len(sum_tokens & src_tokens) / max(len(sum_tokens), 1)
    return overlap_ratio > 0.88


def generate_summary(text: str, api_key: str = "") -> str:
    distil_summary = _summarize_extractive_distilbert(text)
    if not _is_too_close_to_source(distil_summary, text):
        return distil_summary
    groq_summary = _summarize_via_groq(text, api_key)
    if groq_summary and not _is_too_close_to_source(groq_summary, text):
        return groq_summary
    return groq_summary or distil_summary


def extract_from_drugs_bert_multilingual(text: str, candidates: list) -> list:
    if not text or not candidates:
        return []
    uniq = []
    seen = set()
    for c in candidates:
        cl = str(c).strip().lower()
        if len(cl) < 4 or cl in seen:
            continue
        seen.add(cl)
        uniq.append(str(c).strip())
    if not uniq:
        return []
    try:
        tok, mdl  = _get_mbert()
        text_vec  = _encode_transformer_texts([text[:600]], tok, mdl, max_length=192)
        cand_vecs = _encode_transformer_texts(uniq, tok, mdl, max_length=64)
        if len(text_vec) == 0 or len(cand_vecs) == 0:
            return []
        t      = text_vec[0]
        t_norm = np.linalg.norm(t) + 1e-9
        scored = []
        for cand, vec in zip(uniq, cand_vecs):
            sim = float(np.dot(t, vec) / (t_norm * (np.linalg.norm(vec) + 1e-9)))
            scored.append((cand, sim))
        picked = [c for c, s in sorted(scored, key=lambda x: x[1], reverse=True)
                  if s >= 0.55][:6]
        return picked
    except Exception:
        return []


def extract_keywords(text: str) -> list:
    FR_STOPWORDS = {
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "et", "ou", "à", "au", "aux", "en", "dans", "sur", "par",
        "pour", "avec", "sans", "ce", "cette", "ces", "se", "si",
        "qui", "que", "qu", "dont", "où", "mais", "donc", "or", "ni",
        "car", "plus", "très", "bien", "tout", "tous", "toute", "toutes",
        "chez", "après", "lors", "entre", "sous", "vers", "ici", "là",
        "patient", "patients", "médecin", "médecins", "docteur",
        "traitement", "consultation", "note", "visite", "cas",
        "mg", "ml", "cp", "comprimé", "comprimés",
    }

    candidate_text = text
    nlp = get_spacy()
    if nlp is not None:
        try:
            doc = nlp(text[:1500])
            meaningful_tokens = [
                token.text for token in doc
                if token.pos_ in ("NOUN", "PROPN", "ADJ")
                and len(token.text) >= 4
                and token.text.lower() not in FR_STOPWORDS
                and not token.is_punct
                and not token.like_num
            ]
            if len(meaningful_tokens) >= 3:
                candidate_text = " ".join(meaningful_tokens)
        except Exception:
            pass

    keywords: list = []
    try:
        kw_model = get_kw()
        raw = kw_model.extract_keywords(
            candidate_text,
            keyphrase_ngram_range=(1, 2),
            stop_words=list(FR_STOPWORDS),
            top_n=12,
            use_mmr=True,
            diversity=0.6,
        )

        seen_kw: set = set()
        for kw, score in raw:
            if score < 0.28:
                continue
            kw_clean = kw.strip()
            if re.fullmatch(r"[\d\s,.]+", kw_clean):
                continue
            if len(kw_clean) < 4:
                continue
            if kw_clean.lower() in FR_STOPWORDS:
                continue
            key = kw_clean.lower()
            if key in seen_kw:
                continue
            if any(key in k for k in seen_kw):
                continue
            seen_kw.add(key)
            keywords.append(kw_clean)

        keywords = keywords[:8]
    except Exception:
        pass

    return keywords


def find_similar_notes(text: str, df: pd.DataFrame, top_k: int = 3) -> list:
    if df is None or df.empty:
        return []
    try:
        emb       = get_embedder()
        query_vec = emb.encode([text[:512]])
        texts     = df["full_text"].fillna("").tolist()[:500]
        corpus_v  = emb.encode(texts, batch_size=64, show_progress_bar=False)
        sims      = np.dot(corpus_v, query_vec.T).flatten()
        results   = []
        for idx in np.argsort(sims)[::-1][1: top_k + 1]:
            row = df.iloc[idx]
            results.append({
                "text":       str(row.get("full_text", ""))[:200],
                "similarity": round(float(sims[idx]) * 100),
                "rating":     row.get("rating", "N/A"),
            })
        return results
    except Exception:
        return []


def _prioritize_medecins_from_fiche(existing: list, medecin_visite: str) -> list:
    val = medecin_visite.strip()
    if not val:
        return existing
    val       = val.split(",", 1)[0].strip()
    val_clean = re.sub(r"^[Dd][Rr]\.?\s*", "", val).strip()
    canon     = ("Dr. " + val_clean) if val_clean else val
    bn        = val_clean.lower().split()
    tail      = " ".join(bn[-2:]) if len(bn) >= 2 else val_clean.lower()
    kept = []
    for d in existing:
        dl = re.sub(r"^[Dd][Rr]\.?\s*", "", d).strip().lower()
        if not dl:
            continue
        if dl == val_clean.lower() or dl in val_clean.lower() or val_clean.lower() in dl:
            continue
        if tail and (tail == dl or tail in dl or dl.endswith(tail)):
            continue
        kept.append(d)
    return [canon] + kept


def analyze(text: str, models: dict = None, df: pd.DataFrame = None) -> dict:
    text = text.strip()
    if models is None:
        models = {}
    if df is None:
        df = pd.DataFrame()

    if len(text) < 10:
        return {
            "Médicaments":      [],
            "Médecins":         [],
            "Effets":           {},
            "Sentiment":        "neutre",
            "Catégorie":        "Consultation",
            "Résumé":           "Texte insuffisant.",
            "Mots-clés":        [],
            "Notes similaires": [],
            "Fiche_visite":      {},
        }
    fiche    = extract_crm_fiche(text)
    médecins = extract_doctors(text)
    mv = fiche.get("Médecin visité")
    if mv:
        médecins = _prioritize_medecins_from_fiche(médecins, mv)
    result = {
        "Médicaments":      extract_drugs(text, models),
        "Médecins":         médecins,
        "Effets":           extract_effects(text, models),
        "Sentiment":        get_sentiment(text, models),
        "Catégorie":        classify_visit(text),
        "Résumé":           generate_summary(text),
        "Mots-clés":        [],
        "Notes similaires": [],
        "Fiche_visite":      fiche,
    }
    if not FAST_ANALYSIS:
        result["Mots-clés"]        = extract_keywords(text)
        result["Notes similaires"] = find_similar_notes(text, df)
    return result


def split_into_notes(text: str) -> list:
    page_pattern = re.compile(r'---\s*Page\s+\d+(?:\s*\(OCR\))?\s*---', re.IGNORECASE)
    if page_pattern.search(text):
        parts = page_pattern.split(text)
        notes = [p.strip() for p in parts if len(p.strip()) >= 80]
        if len(notes) >= 2:
            return notes

    visit_pattern = re.compile(
        r'(?:^|\n)(?:Visite\s+[Nn]°?\s*\d+|VISITE\s+\d+|Note\s+de\s+visite\s+\d+)',
        re.IGNORECASE | re.MULTILINE
    )
    positions = [m.start() for m in visit_pattern.finditer(text)]
    if len(positions) >= 2:
        notes = []
        for i, start in enumerate(positions):
            end   = positions[i + 1] if i + 1 < len(positions) else len(text)
            chunk = text[start:end].strip()
            if len(chunk) >= 80:
                notes.append(chunk)
        if notes:
            return notes

    tl       = text.lower().strip()
    date_hits = [m.start() for m in re.finditer(r"(?mi)\bDate\s+de\s+visite\b", text)]
    crm_ish   = ("médecin visité" in tl or "médecin visite" in tl) and ("date de visite" in tl)
    if crm_ish and len(date_hits) < 2:
        return [text.strip()] if text.strip() else []
    if crm_ish and len(date_hits) >= 2:
        chunks = []
        for i, start in enumerate(date_hits):
            end   = date_hits[i + 1] if i + 1 < len(date_hits) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
        if chunks:
            return chunks

    sep_pattern = re.compile(r'\n\s*[-=_]{3,}\s*\n')
    if sep_pattern.search(text):
        parts = sep_pattern.split(text)
        notes = [p.strip() for p in parts if len(p.strip()) >= 80]
        if len(notes) >= 2:
            return notes

    blocks = re.split(r'\n{3,}', text)
    if len(blocks) >= 2:
        notes = [b.strip() for b in blocks if len(b.strip()) >= 150]
        if len(notes) >= 2:
            return notes

    return [text.strip()] if text.strip() else []
def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.replace("\x00", " ").split())


def extract_pdf_text(file_path: Path) -> str:
    pages = []

    with pdfplumber.open(str(file_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = clean_text(page.extract_text() or "")
            if text:
                pages.append(f"--- PAGE {i} ---\n{text}")

    return "\n\n".join(pages)


def pdf_to_images(file_path: Path, max_pages: int = 10):
    images = []
    doc = fitz.open(str(file_path))

    for index in range(min(len(doc), max_pages)):
        page = doc[index]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(image)

    doc.close()
    return images


def load_image(file_path: Path):
    return Image.open(file_path).convert("RGB")