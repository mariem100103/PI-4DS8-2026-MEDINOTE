"""
Service FastAPI — Coaching Délégués Médicaux
Migration exacte de coaching_app.py (Streamlit) vers un APIRouter FastAPI.
Expose :
  GET  /coaching/scenarios        → liste des scénarios
  GET  /coaching/levels           → liste des niveaux
  POST /coaching/chat             → envoyer un message
  POST /coaching/final            → obtenir le bilan final
  GET  /coaching/health           → santé du service
"""

import logging
import re
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

# ── Configuration ──────────────────────────────────────────────
GROQ_API_KEY_COACHING = os.environ.get("GROQ_API_KEY_COACHING", os.environ.get("GROQ_API_KEY", "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"))
groq_client_coaching = Groq(api_key=GROQ_API_KEY_COACHING)
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Scénarios (identiques à coaching_app.py) ──────────────────
SCENARIOS = {
    "💬 Discussion libre": {
        "doc_name": "Dr. Dubois",
        "doc_role": "Médecin généraliste",
        "doc_initials": "DD",
        "doc_init": "Bonjour, je vous écoute.",
        "context": (
            "C'est une discussion libre et générale entre le délégué médical et le médecin. "
            "Pas de sujet imposé. Le délégué peut aborder ce qu'il souhaite : présenter un produit, "
            "parler de l'actualité médicale, évoquer des cas patients, créer du lien, etc. "
            "Le médecin répond naturellement selon le niveau de difficulté choisi."
        ),
        "hints": [
            "Se présenter et créer du lien",
            "Écouter et s'adapter au médecin",
            "Apporter de la valeur à chaque échange",
            "Conclure proprement la visite",
        ],
    },
    "🤝 Premier contact": {
        "doc_name": "Dr. Martin",
        "doc_role": "Médecin généraliste",
        "doc_initials": "DM",
        "doc_init": "Oui, entrez. J'ai 5 minutes, pas plus. C'est pour quoi ?",
        "context": (
            "Le délégué arrive pour la PREMIÈRE FOIS. Il doit se présenter, présenter son laboratoire "
            "et son produit. Le médecin n'a aucune information sur le produit. "
            "Les sujets attendus : présentation, accroche, bénéfice patient. "
            "NE PAS aborder prix, effets secondaires ou données cliniques approfondies à moins que le délégué ne les soulève."
        ),
        "hints": [
            "Se présenter clairement (nom, laboratoire, produit)",
            "Demander si c'est le bon moment",
            "Remercier du temps accordé",
            "Accrocher avec un bénéfice patient concret",
        ],
    },
    "💰 Objection prix": {
        "doc_name": "Dr. Lemaire",
        "doc_role": "Cardiologue",
        "doc_initials": "DL",
        "doc_init": "Votre produit est intéressant, mais franchement il coûte beaucoup plus cher que ce que je prescris habituellement. Pourquoi je changerais ?",
        "context": (
            "Le médecin a une objection principale : le PRIX trop élevé par rapport aux alternatives. "
            "Le délégué doit justifier la valeur économique et clinique. "
            "Les sujets attendus : coût-efficacité, observance, résultats long terme, études comparatives, échantillons. "
            "Reste focalisé sur l'objection prix, ne change pas de sujet."
        ),
        "hints": [
            "Valoriser le bénéfice clinique vs coût",
            "Citer une étude comparative",
            "Parler de l'observance et résultats à long terme",
            "Proposer des échantillons ou programme patient",
        ],
    },
    "😤 Médecin hostile": {
        "doc_name": "Dr. Rousseau",
        "doc_role": "Interniste",
        "doc_initials": "DR",
        "doc_init": "Encore un délégué... Je prescris ce que je veux, pas besoin qu'on me dise quoi faire. Qu'est-ce que vous voulez ?",
        "context": (
            "Le médecin est HOSTILE et sur la défensive dès le départ. "
            "Il est irrité par la visite et montre peu d'intérêt. "
            "Le délégué doit désamorcer la tension, rester calme, reconnaître l'expertise du médecin. "
            "Récompense uniquement si le délégué gère bien l'hostilité sans insister lourdement."
        ),
        "hints": [
            "Rester calme et respectueux",
            "Reconnaître son expertise",
            "Apporter de la valeur rapidement",
            "Ne pas insister si refus clair",
        ],
    },
    "🔁 Suivi & fidélisation": {
        "doc_name": "Dr. Benali",
        "doc_role": "Pédiatre",
        "doc_initials": "DB",
        "doc_init": "Ah, rebonjour ! J'ai prescrit votre produit à quelques patients, globalement ça se passe bien. Vous avez des nouveautés ?",
        "context": (
            "C'est une visite de SUIVI. Le médecin connaît déjà le produit et a commencé à le prescrire. "
            "Il est ouvert et attend des nouveautés, retours d'études, matériel patient. "
            "Les sujets attendus : nouvelles données, fidélisation, retours patients, matériel éducatif. "
            "NE PAS refaire une présentation de base du produit."
        ),
        "hints": [
            "Remercier et valoriser la confiance",
            "Présenter une nouveauté ou étude récente",
            "Proposer du matériel éducatif patient",
            "Demander un retour sur les cas traités",
        ],
    },
    "🏥 Spécialiste exigeant": {
        "doc_name": "Dr. Dupont",
        "doc_role": "Neurologue",
        "doc_initials": "DD",
        "doc_init": "Je connais déjà votre molécule. Expliquez-moi pourquoi je devrais la préférer à ce que j'utilise déjà. Soyez précis, j'attends des données.",
        "context": (
            "Le médecin est un SPÉCIALISTE très exigeant qui connaît déjà la molécule. "
            "Il veut des données cliniques précises, des comparaisons avec les concurrents, des sous-groupes. "
            "Les sujets attendus : efficacité comparée, tolérance, études, sous-groupes de patients. "
            "Pénalise les réponses vagues ou sans données chiffrées."
        ),
        "hints": [
            "Citer des données cliniques précises",
            "Comparer les profils d'efficacité/tolérance",
            "Parler des sous-groupes de patients",
            "Rester humble face à son expertise",
        ],
    },
    "📋 Gestion d'un effet indésirable": {
        "doc_name": "Dr. Moreau",
        "doc_role": "Rhumatologue",
        "doc_initials": "DM",
        "doc_init": "J'ai eu un patient qui s'est plaint d'effets secondaires avec votre produit. Ça me fait hésiter à continuer à le prescrire.",
        "context": (
            "Le médecin a eu un cas d'EFFET INDÉSIRABLE avec le produit et hésite à continuer. "
            "Le délégué doit écouter, rassurer avec le profil de tolérance, proposer un suivi. "
            "Les sujets attendus : écoute active, données de tolérance, fréquence des effets, soutien médical. "
            "NE PAS minimiser la plainte du patient. Pénalise si le délégué esquive le sujet."
        ),
        "hints": [
            "Écouter et prendre la plainte au sérieux",
            "Demander des détails sur l'effet secondaire",
            "Rappeler le profil de tolérance global",
            "Proposer un suivi ou support médical",
        ],
    },
}

# ── Niveaux (identiques à coaching_app.py) ────────────────────
LEVELS = {
    1: {
        "label": "🟢 Débutant",
        "badge_class": "level-1",
        "description": "Le médecin est ouvert et coopératif",
        "prompt": (
            "Tu es un médecin globalement coopératif et ouvert. "
            "Tu poses des questions simples, tu es poli et patient. "
            "Tu donnes facilement une chance au délégué de s'exprimer. "
            "Tes objections sont rares et facilement surmontables."
        ),
    },
    2: {
        "label": "🟡 Intermédiaire",
        "badge_class": "level-2",
        "description": "Le médecin est neutre avec quelques objections",
        "prompt": (
            "Tu es un médecin neutre, ni particulièrement accueillant ni hostile. "
            "Tu poses des questions pertinentes et tu soulèves 1 ou 2 objections réalistes. "
            "Tu n'es convaincu que par des arguments solides et des données concrètes. "
            "Tu peux couper court si le délégué tourne autour du pot."
        ),
    },
    3: {
        "label": "🔴 Expert",
        "badge_class": "level-3",
        "description": "Le médecin est difficile, exigeant et sceptique",
        "prompt": (
            "Tu es un médecin très exigeant, sceptique et pressé. "
            "Tu interromps facilement, tu poses des questions pointues sur les données cliniques, "
            "tu compares immédiatement avec les concurrents, tu remets en question chaque argument. "
            "Tu es convaincu SEULEMENT par des réponses très précises et bien structurées. "
            "Tu peux être légèrement condescendant si le délégué hésite ou manque de précision. "
            "Tu mets la pression sur le délégué pour tester sa maîtrise du produit."
        ),
    },
}

# ── Prompts système (identiques à coaching_app.py) ────────────
SYSTEM_TEMPLATE = """Tu es un simulateur de formation pour délégués médicaux pharmaceutiques.
Tu joues le rôle de {doc_name}, {doc_role}.

══════════════════════════════════════════
SCÉNARIO ACTIF : {scenario_name}
══════════════════════════════════════════
{scenario_context}

Ta première phrase dans ce scénario était :
"{doc_init}"
Tu dois rester STRICTEMENT cohérent avec cette ouverture et ce scénario tout au long de la conversation.
NE CHANGE JAMAIS de scénario. Ne mélange pas les sujets d'autres scénarios.

NIVEAU DE DIFFICULTÉ :
{level_prompt}

INSTRUCTIONS STRICTES :
1. Réponds UNIQUEMENT EN TANT QUE LE MÉDECIN (1 à 3 phrases max), en restant dans ton personnage, ton niveau de difficulté ET ton scénario.
2. {feedback_instruction}
3. TOUJOURS en français. Sois exigeant mais constructif dans le feedback.
4. Le médecin évolue selon la qualité des réponses : il s'adoucit si convaincu, s'impatiente si les réponses sont faibles ou hors sujet.
5. Au niveau Expert, pose souvent des contre-questions sur les données, les études, les effets secondaires.

{feedback_format}"""

FEEDBACK_FORMAT_STANDARD = """Le feedback de coach doit contenir :
   - Un score STRICT sur 10 :
     * Pénalise (−2 à −4 pts) si la réponse est hors sujet par rapport au scénario "{scenario_name}"
     * Pénalise (−1 à −2 pts) si le délégué introduit des éléments qui n'ont pas de rapport avec ce scénario
     * Récompense uniquement les éléments pertinents pour CE scénario précis
   - Ce qui était bien ✓
   - Ce qui peut être amélioré ✗
   - 1 conseil concret et actionnable 💡

FORMAT EXACT À RESPECTER (NE PAS DÉVIER) :
[réplique du médecin en 1-3 phrases]

[FEEDBACK]Score : X/10 | ✓ [point positif] | ✗ [point à améliorer] | 💡 [conseil concret][/FEEDBACK]

IMPORTANT : Tu dois TOUJOURS inclure les balises [FEEDBACK] et [/FEEDBACK] dans ta réponse."""

FEEDBACK_FORMAT_FINAL = """FORMAT EXACT À RESPECTER POUR LE BILAN FINAL :
[réplique de congé du médecin en 1-2 phrases]

[FEEDBACK]
NOTE FINALE : X/10

🏆 Points forts de la visite :
[liste des points forts]

⚠️ Points à améliorer :
[liste des points à améliorer]

💬 Impression générale :
[ce que le médecin a pensé de cette visite]

💡 Conseil principal pour progresser :
[un conseil actionnable]
[/FEEDBACK]

IMPORTANT : Tu dois TOUJOURS inclure les balises [FEEDBACK] et [/FEEDBACK] dans ta réponse."""


# ── Schemas Pydantic ──────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: list[Message]
    scenario_key: str
    level: int
    force_final_score: bool = False

class ChatResponse(BaseModel):
    doc_reply: str
    feedback: str | None
    score: int | None


# ── Logique (identique à coaching_app.py) ─────────────────────
def call_groq(history: list, scenario_key: str, level: int, force_final_score: bool = False) -> str:
    sc = SCENARIOS[scenario_key]
    lv = LEVELS[level]
    is_libre = scenario_key == "💬 Discussion libre"

    if force_final_score:
        feedback_instruction = (
            "Le délégué vient de terminer la visite. "
            "Réponds avec une courte phrase de congé naturelle, puis donne dans [FEEDBACK][/FEEDBACK] "
            "la NOTE FINALE GLOBALE sur 10 avec le bilan complet de toute la visite."
        )
        feedback_format = FEEDBACK_FORMAT_FINAL
    elif is_libre:
        feedback_instruction = (
            "NE PAS inclure de feedback après ta réplique. "
            "Réponds UNIQUEMENT en tant que médecin, SANS les balises [FEEDBACK]. "
            "Le bilan sera donné uniquement à la fin de la visite."
        )
        feedback_format = "(Aucun feedback dans ce scénario, sauf bilan final.)"
    else:
        feedback_instruction = (
            "Après ta réplique de médecin, saute une ligne, puis écris le feedback entre [FEEDBACK] et [/FEEDBACK]."
        )
        feedback_format = FEEDBACK_FORMAT_STANDARD.format(scenario_name=scenario_key)

    system_prompt = SYSTEM_TEMPLATE.format(
        doc_name=sc["doc_name"],
        doc_role=sc["doc_role"],
        scenario_name=scenario_key,
        scenario_context=sc["context"],
        doc_init=sc["doc_init"],
        level_prompt=lv["prompt"],
        feedback_instruction=feedback_instruction,
        feedback_format=feedback_format,
    )

    messages = [{"role": "system", "content": system_prompt}]
    history_without_init = history[1:] if history and history[0]["role"] == "assistant" else history
    for msg in history_without_init:
        messages.append({"role": msg["role"], "content": msg["content"]})

    response = groq_client_coaching.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=600,
        temperature=0.7,
        timeout=30,
    )
    return response.choices[0].message.content


def parse_response(full_text: str):
    feedback_match = re.search(r"\[FEEDBACK\]([\s\S]*?)\[/FEEDBACK\]", full_text, re.IGNORECASE)
    feedback = feedback_match.group(1).strip() if feedback_match else None
    doc_reply = re.sub(r"\[FEEDBACK\][\s\S]*?\[/FEEDBACK\]", "", full_text, flags=re.IGNORECASE).strip()
    doc_reply = re.sub(r"\n{3,}", "\n\n", doc_reply).strip()
    if feedback is None and "\n\n" in full_text:
        parts = full_text.split("\n\n", 1)
        doc_reply = parts[0].strip()
        if len(parts) > 1 and ("Score" in parts[1] or "✓" in parts[1] or "💡" in parts[1]):
            feedback = parts[1].strip()
    return doc_reply, feedback


def extract_score(feedback: str):
    if not feedback:
        return None
    m = re.search(r"(\d+)\s*/\s*10", feedback)
    return int(m.group(1)) if m else None


# ── Routes FastAPI ─────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "module": "coaching_medical"}


@router.get("/scenarios")
async def get_scenarios():
    """Retourne la liste des scénarios avec leurs métadonnées."""
    result = {}
    for key, sc in SCENARIOS.items():
        result[key] = {
            "doc_name": sc["doc_name"],
            "doc_role": sc["doc_role"],
            "doc_initials": sc["doc_initials"],
            "doc_init": sc["doc_init"],
            "hints": sc["hints"],
        }
    return result


@router.get("/levels")
async def get_levels():
    """Retourne la liste des niveaux de difficulté."""
    return {
        str(k): {
            "label": v["label"],
            "badge_class": v["badge_class"],
            "description": v["description"],
        }
        for k, v in LEVELS.items()
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Envoyer un message et recevoir la réponse du médecin + feedback."""
    if request.scenario_key not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Scénario inconnu : {request.scenario_key}")
    if request.level not in LEVELS:
        raise HTTPException(status_code=400, detail=f"Niveau inconnu : {request.level}")
    import time
    for attempt in range(3):
        
     try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        full_text = call_groq(history, request.scenario_key, request.level, request.force_final_score)
        doc_reply, feedback = parse_response(full_text)
        score = extract_score(feedback)
        return ChatResponse(doc_reply=doc_reply, feedback=feedback, score=score)
     except Exception as e:
        err = str(e).lower()
        if attempt < 2 and ("timeout" in err or "timed out" in err):
                wait = 2 ** attempt 
                logger.warning(f"⚠️ Timeout tentative {attempt+1}/3, retry dans {wait}s")
                time.sleep(wait)
        else:
                logger.error(f"Erreur coaching chat : {e}")
                raise HTTPException(status_code=500, detail=str(e))