import os
import io
import json
import base64
from typing import Dict, Any, List
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEYY"))

TEXT_MODEL = os.getenv("TEXT_MODEL", "openai/gpt-oss-20b")
VISION_MODEL = os.getenv("VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")


def image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def read_image_with_groq(image: Image.Image) -> str:
    image_b64 = image_to_base64(image)

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Lis tout le texte visible dans cette image. Ne résume pas."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrais le texte complet de ce rapport."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0,
        max_tokens=2048
    )

    return response.choices[0].message.content


def format_text_to_report_json(extracted_text: str) -> Dict[str, Any]:
    prompt = f"""
Tu es un assistant d'extraction pour un rapport de délégué médical.

Retourne uniquement un JSON valide avec ce template:

{{
  "nom_prospect": null,
  "date_visite": null,
  "objectif_visite": null,
  "produits_presentes": [
    {{
      "nom": null,
      "commentaire": null,
      "opportunites": null,
      "benchmarking_concurrents": [],
      "nombre_echantillons": null
    }}
  ],
  "commentaire": null,
  "opportunites": null,
  "benchmarking_concurrents": [],
  "nombre_echantillons": null,
  "nom_superviseur": null,
  "nombre_patients_presents": null,
  "gadget": null,
  "remarque_generale": null,
  "date_relance": null,
  "prochaine_etape": null
}}

Règles:
- Ne pas inventer.
- Si une information manque, mets null ou [].
- Garde les phrases complètes.
- Le texte peut venir d'un PDF ou d'une image.

Texte:
{extracted_text}
"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Tu réponds uniquement avec JSON valide."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)