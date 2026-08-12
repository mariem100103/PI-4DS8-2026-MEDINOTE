# -*- coding: utf-8 -*-
"""
MedAssist IA — Chatbot intelligent pour les médicaments
Backend FastAPI — service chatbot
"""

from dotenv import load_dotenv
load_dotenv()

import re
import numpy as np
import pandas as pd
import faiss
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer
import json
import unicodedata
from symspellpy import SymSpell, Verbosity
from google import genai
import os
import time

file_path = "models/medicaments_final.xlsx"
df = pd.read_excel(file_path)
df.head()

df = df.copy()

# Normalize column names just in case
df.columns = [c.strip().upper() for c in df.columns]

# Expected columns in your file:
expected_cols = [
    'CODE_PCT', 'NOM_COMMERCIAL', 'DCI', 'AP', 'CATEGORIE',
    'PRIX_PUBLIC', 'TARIF_REFERENCE', 'FORME',
    'QUANTITE_VAL', 'UNITE_QUANTITE', 'VALEUR_DOSAGE', 'UNITE_DOSAGE'
]

missing = [c for c in expected_cols if c not in df.columns]
print("Missing columns:", missing)

def clean_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip().upper()

def clean_price(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().replace(" ", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return np.nan

text_cols = ['NOM_COMMERCIAL', 'DCI', 'AP', 'CATEGORIE', 'FORME', 'UNITE_QUANTITE', 'VALEUR_DOSAGE', 'UNITE_DOSAGE']
for col in text_cols:
    df[col] = df[col].apply(clean_text)

df['PRIX_PUBLIC_NUM'] = df['PRIX_PUBLIC'].apply(clean_price)
df['TARIF_REFERENCE_NUM'] = df['TARIF_REFERENCE'].apply(clean_price)
df['QUANTITE_VAL'] = pd.to_numeric(df['QUANTITE_VAL'], errors='coerce')

# Composite columns for matching
df['DOSAGE_FULL'] = (
    df['VALEUR_DOSAGE'].fillna('') + ' ' + df['UNITE_DOSAGE'].fillna('')
).str.strip()

df['QUANTITE_FULL'] = (
    df['QUANTITE_VAL'].fillna('').astype(str).str.replace('.0', '', regex=False) + ' ' + df['UNITE_QUANTITE'].fillna('')
).str.strip()

df['DISPLAY_NAME'] = df['NOM_COMMERCIAL'].fillna('') + " | " + df['DCI'].fillna('')

print(df.shape)
df.head(3)

def build_profile(row):
    return f"""
Commercial name: {row['NOM_COMMERCIAL']}
DCI: {row['DCI']}
Category: {row['CATEGORIE']}
Form: {row['FORME']}
Dosage: {row['DOSAGE_FULL']}
Quantity: {row['QUANTITE_FULL']}
Public price: {row['PRIX_PUBLIC_NUM']}
Reference tariff: {row['TARIF_REFERENCE_NUM']}
AP: {row['AP']}
Code: {row['CODE_PCT']}
""".strip()

df['PROFILE_TEXT'] = df.apply(build_profile, axis=1)
df[['NOM_COMMERCIAL', 'DCI', 'PROFILE_TEXT']].head(2)

"""---
# Phase 4 — Modélisation

## 4.1 Présentation des modèles et outils utilisés

Le système MedAssist IA repose sur une **architecture hybride multi-composants**. Chaque composant joue un rôle précis dans le pipeline de traitement des requêtes utilisateur.

---

### 🔹 Composant 1 — Correction orthographique : SymSpell

**SymSpell** est un algorithme de correction orthographique ultra-rapide basé sur la génération de variantes par suppression de caractères (*delete-only pre-computation*). Il est utilisé ici pour corriger les fautes de frappe dans les noms de médicaments avant toute recherche.

- **Entrée** : requête brute de l'utilisateur (ex: *"brufeen"*)
- **Sortie** : requête corrigée (ex: *"brufen"*)
- **Distance d'édition maximale** : 2 caractères
- **Dictionnaire** : construit dynamiquement à partir des noms commerciaux et DCI du dataset

---

### 🔹 Composant 2 — Correspondance floue : RapidFuzz

**RapidFuzz** est une librairie de *fuzzy string matching* basée sur la distance de Levenshtein et ses variantes (WRatio, partial ratio...). Elle permet d'identifier le nom commercial le plus proche de ce que l'utilisateur a tapé.

- **Algorithme utilisé** : WRatio (weighted ratio — combine plusieurs méthodes)
- **Seuil de confiance** : 88% minimum pour valider une correspondance
- **Rôle** : résolution d'entité (ex: *"adol"* → *ADOL* dans le dataset)

---

### 🔹 Composant 3 — Embeddings sémantiques : Sentence-Transformers (MiniLM-L6-v2)

**all-MiniLM-L6-v2** est un modèle de *sentence embeddings* pré-entraîné, disponible sur HuggingFace. Il encode chaque texte en un vecteur de dimension 384, permettant de mesurer la similarité sémantique entre deux phrases.

- **Architecture** : Transformer (6 couches, 22M paramètres)
- **Dimension des vecteurs** : 384
- **Usage** : chaque profil médicament du dataset est encodé en vecteur → stocké dans l'index FAISS
- **Avantage** : comprend le sens des requêtes, pas seulement les mots exacts

---

### 🔹 Composant 4 — Indexation vectorielle : FAISS

**FAISS** (*Facebook AI Similarity Search*) est une librairie optimisée pour la recherche de vecteurs similaires à grande échelle. Elle permet de retrouver rapidement les médicaments sémantiquement proches d'une requête.

- **Type d'index** : `IndexFlatIP` (produit scalaire, équivalent cosine après normalisation L2)
- **Normalisation** : L2 appliquée sur tous les vecteurs avant indexation
- **Top-K** : les 5 résultats les plus proches sont retournés
- **Taille de l'index** : 3315 vecteurs (un par ligne du dataset)

---

### 🔹 Composant 5 — Génération de réponse : Gemini 2.5 Flash (Google)

**Gemini 2.5 Flash** est le modèle de langage (LLM) utilisé pour transformer les données structurées récupérées du dataset en réponse naturelle et professionnelle.

- **Rôle** : génération de texte à partir d'un contexte fourni (RAG — Retrieval-Augmented Generation)
- **Prompting** : le modèle reçoit uniquement les données du dataset dans son contexte → il ne peut pas halluciner d'informations absentes
- **Tâches gérées** : comparaison, alternative moins chère, résumé d'information, alternatives plus sûres
- **Fallback** : si le LLM échoue ou retourne une réponse vide, une réponse structurée est générée sans LLM

---

### 🔹 Composant 6 — Scoring des effets indésirables (module custom)

Un **lexique personnalisé** a été construit pour évaluer la "lourdeur" du profil d'effets indésirables d'un médicament. Chaque effet est classé en trois niveaux :

| Niveau | Exemples | Poids |
|--------|----------|-------|
| Léger  | irritation, picotements, rougeur | 1.0 |
| Modéré | nausées, vertiges, fatigue, prurit | 2.5 |
| Sévère | convulsions, hémorragie, dyspnée, allergie | 5.0 |

- **Usage** : permet d'identifier l'alternative avec moins d'effets indésirables parmi les médicaments de même DCI
- **Score final** : somme pondérée des effets détectés + bonus de diversité des systèmes touchés

---
## 4.2 Justification du choix des modèles

### Pourquoi SymSpell plutôt qu'un autre correcteur ?

| Critère | SymSpell | TextBlob | Hunspell |
|---------|----------|----------|----------|
| Vitesse |  Très rapide (O(1) lookup) |  Lent |  Moyen |
| Dictionnaire custom |  Oui |  Non |  Limité |
| Noms propres médicaux |  Oui (on le construit) |  Non |  Non |
| Intégration Python |  Simple |  Simple |  Complexe |

**→ SymSpell est retenu** car il permet de construire un dictionnaire personnalisé à partir des noms de médicaments du dataset, ce qu'aucune autre librairie ne fait nativement.

---

### Pourquoi all-MiniLM-L6-v2 plutôt qu'un autre modèle d'embeddings ?

| Critère | MiniLM-L6-v2 | paraphrase-mpnet | multilingual-e5 |
|---------|-------------|------------------|-----------------|
| Taille | 22M params  | 110M params  | 278M params  |
| Vitesse d'encodage |  Rapide |  Lent |  Très lent |
| Score SBERT benchmark | 68.1 | 69.5 | 70.2 |
| Multilingual |  Non |  Non |  Oui |
| Adapté à notre usage |  Oui |  Surdimensionné |  Surdimensionné |

**→ MiniLM-L6-v2 est retenu** car il offre le meilleur compromis vitesse/performance pour un dataset de taille modeste (3315 médicaments). La différence de score avec des modèles plus lourds est minime (< 2%), mais le gain en vitesse est significatif.

---

### Pourquoi FAISS plutôt qu'une recherche naïve ?

| Critère | FAISS | Recherche brute (numpy) | Elasticsearch |
|---------|-------|------------------------|---------------|
| Complexité recherche | O(n) optimisé | O(n) | O(log n) |
| Scalabilité |  Millions de vecteurs |  Limité |  Oui |
| Installation |  pip simple |  Natif |  Serveur requis |
| Support GPU |  Optionnel |  Non |  Non |

**→ FAISS est retenu** car il est conçu spécifiquement pour la recherche vectorielle, s'intègre facilement en Python, et reste performant même si le dataset venait à grandir.

---

### Pourquoi Gemini 2.5 Flash plutôt que GPT-4 ou un modèle local ?

| Critère | Gemini 2.5 Flash | GPT-4o | Mistral (local) |
|---------|-----------------|--------|------------------|
| Coût |  Gratuit (quota) |  Payant |  Gratuit |
| Qualité de réponse |  Très bonne |  Excellente |  Variable |
| Vitesse |  Rapide |  Moyen |  Rapide (local) |
| Dépendance réseau |  Oui |  Oui |  Non |
| Accessibilité |  API simple |  Compte requis |  GPU recommandé |

**→ Gemini 2.5 Flash est retenu** pour son excellent rapport qualité/coût (quota gratuit suffisant pour les tests), sa vitesse de réponse, et la simplicité de son API Python (`google-genai`).

---

### Architecture globale du pipeline

```
Requête utilisateur
        ↓
  [SymSpell] → Correction orthographique
        ↓
  [RapidFuzz] → Résolution du nom de médicament
        ↓
  [Analyse d'intention] → Prix / Dosage / Comparaison / Alternative...
        ↓
  [FAISS + MiniLM] → Recherche sémantique (si fuzzy insuffisant)
        ↓
  [Dataset] → Récupération des données structurées
        ↓
  [Gemini 2.5 Flash] → Génération de la réponse naturelle
        ↓
  Réponse finale à l'utilisateur
```

---
## 4.3 Références aux performances théoriques et complexité des modèles

### Performances théoriques connues

#### all-MiniLM-L6-v2 — Benchmark SBERT
Le modèle est évalué sur le benchmark **SBERT** (*Semantic Textual Similarity*) :

| Benchmark | Score MiniLM-L6-v2 | Score BERT-base |
|-----------|-------------------|-----------------|
| STS-B (Spearman) | 68.1 | 65.2 |
| STS-12 à STS-16 (moyenne) | 67.3 | 63.9 |
| Vitesse (séq/sec) | ~14 000 | ~4 000 |

> Source : [SBERT.net — Pretrained Models](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html)

---

#### FAISS — Complexité algorithmique

| Type d'index | Complexité recherche | Mémoire | Précision |
|-------------|---------------------|---------|----------|
| `IndexFlatIP` *(utilisé)* | O(n × d) | Élevée | 100% exacte |
| `IndexIVFFlat` | O(n/k × d) | Moyenne | ~95% |
| `IndexHNSW` | O(log n) | Élevée | ~99% |

**Choix** : `IndexFlatIP` est utilisé car notre dataset est petit (3315 entrées). La recherche exhaustive exacte est réalisable en temps réel sans approximation.

> Source : [FAISS Documentation — Guidelines](https://faiss.ai/guidelines.html)

---

#### SymSpell — Complexité

| Opération | SymSpell | Levenshtein classique |
|-----------|----------|-----------------------|
| Pré-calcul | O(n × d!) | — |
| Recherche à la volée | **O(1)** | O(n × m²) |

SymSpell est **1 million de fois plus rapide** que l'approche Levenshtein classique grâce à sa technique de *delete-only pre-computation*.

> Source : [SymSpell GitHub — Wolf Garbe](https://github.com/wolfgarbe/SymSpell)

---

#### RapidFuzz — Complexité

| Métrique | Complexité | Usage dans le projet |
|----------|------------|----------------------|
| Levenshtein distance | O(m × n) | Résolution d'entité |
| WRatio | O(m × n) | Matching médicament |
| `process.extractOne` | O(k × m × n) | Top-1 résultat |

Avec k = 3315 noms dans le dataset et des noms courts (m, n ≤ 30 caractères), le calcul reste très rapide (< 10 ms par requête).

> Source : [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/)

---

### Résumé — Complexité globale du pipeline

| Étape | Modèle | Complexité | Temps estimé |
|-------|--------|------------|-------------|
| Correction orthographique | SymSpell | O(1) | < 1 ms |
| Résolution d'entité | RapidFuzz | O(k × m × n) | < 10 ms |
| Encodage requête | MiniLM-L6-v2 | O(L²) (attention) | ~20 ms |
| Recherche vectorielle | FAISS IndexFlatIP | O(n × d) | < 5 ms |
| Génération réponse | Gemini 2.5 Flash | — (API externe) | 500–2000 ms |
| **Total estimé** | | | **~0.5 à 2 secondes** |

> Le goulot d'étranglement principal est l'appel API à Gemini. Le reste du pipeline (recherche, correction, matching) s'exécute en moins de 50 ms au total.
"""

model_name = "sentence-transformers/all-MiniLM-L6-v2"
embedder = SentenceTransformer(model_name)

documents = df['PROFILE_TEXT'].tolist()
embeddings = embedder.encode(documents, convert_to_numpy=True, show_progress_bar=True)

# Normalize for cosine similarity via inner product
faiss.normalize_L2(embeddings)

dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)

print("FAISS index size:", index.ntotal)

medicine_names = df['NOM_COMMERCIAL'].dropna().unique().tolist()

def fuzzy_find_medicine_name(query, limit=5):
    matches = process.extract(
        query.upper(),
        medicine_names,
        scorer=fuzz.WRatio,
        limit=limit
    )
    return matches

def get_rows_by_name(name):
    sub = df[df['NOM_COMMERCIAL'] == name.upper()].copy()
    return sub.sort_values(by='PRIX_PUBLIC_NUM', ascending=True)

def semantic_search(query, top_k=5):
    q_emb = embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    scores, indices = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        row = df.iloc[idx]
        results.append({
            "score": float(score),
            "NOM_COMMERCIAL": row['NOM_COMMERCIAL'],
            "DCI": row['DCI'],
            "FORME": row['FORME'],
            "DOSAGE_FULL": row['DOSAGE_FULL'],
            "PRIX_PUBLIC_NUM": row['PRIX_PUBLIC_NUM'],
            "PROFILE_TEXT": row['PROFILE_TEXT']
        })
    return results

#Normalisation


def strip_accents(text):
    text = str(text)
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )

def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower().strip()
    text = strip_accents(text)
    text = text.replace("-", " ")
    text = text.replace("/", " / ")
    text = re.sub(r"[^\w\s%+/.,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



def normalize_user_query(query):
    q = str(query).strip().lower()

    for wrong, right in MANUAL_CORRECTIONS.items():
        q = q.replace(wrong, right)

    q = correct_query_with_symspell(q)
    q = re.sub(r"\s+", " ", q).strip()
    return q

# Correction orthographique

COMMON_WORDS = [
    "médicament", "médicaments", "medicament", "medicaments",
    "dosage", "prix", "forme", "formes", "dci", "catégorie", "categorie",
    "principe", "actif", "principe actif",
    "moins", "cher", "chère", "chere", "alternative", "équivalent", "equivalent",
    "compare", "comparer", "avec",
    "sirop", "comprimé", "comprime", "gelule", "gélule", "poudre", "collyre", "crème", "creme",
    "parle", "parle-moi", "parle moi", "informations", "information", "infos", "info",
    "même", "meme", "quel", "quels", "quelle", "quelles",
    "donne", "montre", "trouve", "cherche", "coûte", "coute", "prix","difference", "différence", "entre"
]

MANUAL_CORRECTIONS = {
    "medicment": "médicament",
    "medicament": "médicament",
    "medicaments": "médicaments",
    "dosag": "dosage",
    "compime": "comprimé",
    "comprimee": "comprimé",
    "meme": "même",
    "moin cher": "moins cher",
    "moin chère": "moins chère",
    "moin chere": "moins chère",
    "pricipe actif": "principe actif",
    "prinicpe actif": "principe actif",

    # fautes fréquentes médicaments
    "brufeen": "brufen",
    "doliprne": "doliprane",
    "efferalgane": "efferalgan",
    "acyryl": "aciryl",
    "aciril": "aciryl",
}
MEDICINE_ALIASES = {
    "brufeen": "BRUFEN",
    "bruffen": "BRUFEN",
    "bruufen": "BRUFEN",
    "doliprne": "DOLIPRANE",
    "doliprnae": "DOLIPRANE",
    "efferalgane": "EFFERALGAN",
    "acyryl": "ACIRYL",
    "aciril": "ACIRYL",
}

def build_symspell_from_dataset(df):
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    vocabulary = set()

    for word in COMMON_WORDS:
        for token in normalize_text(word).split():
            if token:
                vocabulary.add(token)

    if "NOM_COMMERCIAL" in df.columns:
        for name in df["NOM_COMMERCIAL"].dropna().astype(str):
            norm_name = normalize_text(name)
            if norm_name:
                vocabulary.add(norm_name)
            for token in norm_name.split():
                if token:
                    vocabulary.add(token)

    if "DCI" in df.columns:
        for dci in df["DCI"].dropna().astype(str):
            for token in re.split(r"[\s+/,\-]+", normalize_text(dci)):
                if token:
                    vocabulary.add(token)

    if "FORME" in df.columns:
        for form in df["FORME"].dropna().astype(str):
            for token in normalize_text(form).split():
                if token:
                    vocabulary.add(token)

    if "CATEGORIE" in df.columns:
        for cat in df["CATEGORIE"].dropna().astype(str):
            for token in normalize_text(cat).split():
                if token:
                    vocabulary.add(token)

    for word in vocabulary:
        word = word.strip()
        if len(word) >= 2:
            sym_spell.create_dictionary_entry(word, 1)

    return sym_spell

sym_spell = build_symspell_from_dataset(df)

medicine_names_original = []
medicine_names_normalized = []
medicine_norm_to_original = {}

if "NOM_COMMERCIAL" in df.columns:
    for name in df["NOM_COMMERCIAL"].dropna().astype(str).unique().tolist():
        norm_name = normalize_text(name)
        medicine_names_original.append(name)
        medicine_names_normalized.append(norm_name)
        if norm_name not in medicine_norm_to_original:
            medicine_norm_to_original[norm_name] = name


def correct_query_with_symspell(query):
    tokens = normalize_text(query).split()
    corrected_tokens = []

    medicine_tokens = set()
    for med in medicine_names_normalized:
        for tok in med.split():
            medicine_tokens.add(tok)

    for token in tokens:
        if re.search(r"\d", token):
            corrected_tokens.append(token)
            continue

        if token in {
   "mg", "g", "ml", "mcg", "%", "/", "vs",
   "difference", "différence", "entre",
   "quelle", "est", "la", "comparaison", "compare", "comparer",
   "prix", "dosage", "forme", "dci", "info", "infos", "parle",
   "medicament", "médicament"
}:
         corrected_tokens.append(token)
         continue

        if len(token) <= 2:
            corrected_tokens.append(token)
            continue

        if token in medicine_tokens:
            corrected_tokens.append(token)
            continue

        suggestions = sym_spell.lookup(token, Verbosity.CLOSEST, max_edit_distance=2)

        if suggestions:
            best = suggestions[0].term
            if fuzz.ratio(token, best) >= 70:
                corrected_tokens.append(best)
            else:
                corrected_tokens.append(token)
        else:
            corrected_tokens.append(token)

    return " ".join(corrected_tokens)

# DOSAGE FUNCTIONS
def extract_dosage(query):
    q = str(query).upper().replace(",", ".").strip()

    match = re.search(r'(\d+(?:[./]\d+)?)\s*(MG/ML|MG|G|ML|MCG|%)', q)
    if match:
        return f"{match.group(1)} {match.group(2)}"

    return None

# FOLLOW-UP HELPERS

def extract_compare_medicines(query):
    q = normalize_user_query(query)

    patterns = [
        r"^\s*(.+?)\s+vs\s+(.+?)\s*$",
        r"^\s*(?:compare|comparer)\s+(.+?)\s+(?:avec|et|vs)\s+(.+?)\s*$",
        r"^\s*(?:difference entre|différence entre)\s+(.+?)\s+(?:et|vs)\s+(.+?)\s*$",
        r"^\s*(?:quelle difference entre|quelle différence entre)\s+(.+?)\s+(?:et|vs)\s+(.+?)\s*$",
        r"^\s*(?:quelle est la difference entre|quelle est la différence entre)\s+(.+?)\s+(?:et|vs)\s+(.+?)\s*$",
        r"^\s*(?:c est quoi la difference entre|c'est quoi la difference entre|c est quoi la différence entre|c'est quoi la différence entre)\s+(.+?)\s+(?:et|vs)\s+(.+?)\s*$",
    ]

    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            med1 = match.group(1).strip(" ?.:,;")
            med2 = match.group(2).strip(" ?.:,;")
            return med1, med2

    return None, None

#Résolution d’entités
def extract_medicine_from_full_query(query):
    q = normalize_user_query(query)

    patterns = [
        # requêtes simples
        r"(?:prix de|prix du|prix des|donne moi le prix de|quel est le prix de|combien coute|combien coûte)\s+(.+)",
        r"(?:dosage de|dosage du|dosage des|quel est le dosage de|donne moi le dosage de)\s+(.+)",
        r"(?:forme de|formes de|quelles sont les formes de|quelle est la forme de|sous quelle forme existe)\s+(.+)",
        r"(?:dci de|principe actif de|quel est le principe actif de|quelle est la dci de)\s+(.+)",
        r"(?:parle moi de|parle moi du|parle moi des|parle de|info sur|infos sur|informations sur)\s+(.+)",

        # alternatives / équivalents
        r"(?:alternative a|alternative à)\s+(.+?)(?:\s+(?:mieux tolere|mieux toléré|avec moins d effets|avec moins d'effets|avec moins d effets secondaires|avec moins d'effets secondaires|moins chere|moins chère|moins cher)|$)",
        r"(?:equivalent de|équivalent de|equivalent a|équivalent à)\s+(.+?)(?:\s+(?:mieux tolere|mieux toléré|avec moins d effets|avec moins d'effets|avec moins d effets secondaires|avec moins d'effets secondaires|moins chere|moins chère|moins cher)|$)",
        r"(?:meme dci que|même dci que)\s+(.+?)(?:\s+(?:mais|avec|mieux tolere|mieux toléré)|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" ?.:,;")
            return candidate

    return q

def is_match_reliable(candidate_norm, matched_norm, min_ratio=88):
    if not candidate_norm or not matched_norm:
        return False
    return fuzz.ratio(candidate_norm, matched_norm) >= min_ratio


def resolve_medicine_name(user_text, threshold=92):
    if "NOM_COMMERCIAL" not in df.columns:
        return None, None

    raw_text = str(user_text).strip()
    candidate = extract_medicine_from_full_query(raw_text)
    candidate = correct_query_with_symspell(candidate)
    candidate_norm = normalize_text(candidate)

    if not candidate_norm:
        return None, None

    # sécurité : on refuse les candidats trop courts
    if len(candidate_norm) < 4:
        return None, None

    # 1. exact match
    if candidate_norm in medicine_norm_to_original:
        return medicine_norm_to_original[candidate_norm], "exact_norm"

    # 2. fuzzy fort sur toute la chaîne
    if medicine_names_normalized:
        match = process.extractOne(candidate_norm, medicine_names_normalized, scorer=fuzz.WRatio)
        if match and match[1] >= threshold:
            matched_norm = match[0]
            if is_match_reliable(candidate_norm, matched_norm, min_ratio=88):
                return medicine_norm_to_original.get(matched_norm, matched_norm.upper()), "fuzzy_norm"

    # 3. token-level fuzzy seulement pour des tokens assez longs
    candidate_tokens = [tok for tok in candidate_norm.split() if len(tok) >= 5]
    for tok in candidate_tokens:
        match = process.extractOne(tok, medicine_names_normalized, scorer=fuzz.WRatio)
        if match and match[1] >= 95:
            matched_norm = match[0]
            if is_match_reliable(tok, matched_norm, min_ratio=90):
                return medicine_norm_to_original.get(matched_norm, matched_norm.upper()), "token_fuzzy"

    return None, None

def get_rows_by_name(name):
    if not name or "NOM_COMMERCIAL" not in df.columns:
        return pd.DataFrame()

    resolved_name, _ = resolve_medicine_name(name)
    final_name = resolved_name if resolved_name else str(name)

    return df[
        df["NOM_COMMERCIAL"].fillna("").astype(str).str.upper() == str(final_name).upper()
    ].copy()

def extract_reference_medicine_for_safer_alternative(query):
    q = normalize_user_query(query)

    patterns = [
        r"(?:meme dci que|même dci que)\s+(.+?)(?:\s+(?:mais|avec|mieux tolere|mieux toléré)|$)",
        r"(?:equivalent a|équivalent à|equivalent de|équivalent de)\s+(.+?)(?:\s+(?:avec|mais|mieux tolere|mieux toléré)|$)",
        r"(?:alternative a|alternative à|alternative de)\s+(.+?)(?:\s+(?:avec|mais|mieux tolere|mieux toléré)|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" ?.:,;")
            resolved_name, _ = resolve_medicine_name(candidate)
            if resolved_name:
                return resolved_name

    return extract_explicit_medicine_from_query(q)


def extract_explicit_medicine_from_query(query):
    """
    Retourne un médicament seulement si la requête contient
    vraiment un nom de médicament explicite.
    Pour les follow-ups ou comparaisons, on évite les faux positifs.
    """
    q = normalize_user_query(query)

    # comparaison => pas un single medicine
    if (
        "compare" in q
        or "comparer" in q
        or "difference entre" in q
        or "différence entre" in q
        or "quelle difference entre" in q
        or "quelle différence entre" in q
        or " vs " in f" {q} "
    ):
        return None

    # follow-up => ne pas essayer de détecter un médicament explicite
    if is_followup_query(q):
        return None

    patterns = [
        r"(?:parle moi de|parle moi du|parle moi des|parle de|info sur|infos sur|informations sur)\s+(.+)",
        r"(?:prix de|prix du|prix des|donne moi le prix de|quel est le prix de|combien coute|combien coûte)\s+(.+)",
        r"(?:dosage de|dosage du|dosage des|quel est le dosage de|donne moi le dosage de)\s+(.+)",
        r"(?:forme de|formes de|quelles sont les formes de|quelle est la forme de|sous quelle forme existe)\s+(.+)",
        r"(?:dci de|principe actif de|quel est le principe actif de|quelle est la dci de)\s+(.+)",
        r"(?:alternative moins chere a|alternative moins cher a|moins chere que|moins cher que)\s+(.+)",
        r"(?:alternative a|alternative à)\s+(.+?)(?:\s+(?:mieux tolere|mieux toléré|avec moins d effets|avec moins d'effets|avec moins d effets secondaires|avec moins d'effets secondaires)|$)",
        r"(?:equivalent de|équivalent de|equivalent a|équivalent à)\s+(.+?)(?:\s+(?:mieux tolere|mieux toléré|avec moins d effets|avec moins d'effets|avec moins d effets secondaires|avec moins d'effets secondaires)|$)",
        r"(?:meme dci que|même dci que)\s+(.+?)(?:\s+(?:mais|avec|mieux tolere|mieux toléré)|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" ?.:,;")
            resolved_name, _ = resolve_medicine_name(candidate)
            if resolved_name:
                return resolved_name

    # fallback global seulement pour des phrases assez longues
    tokens = q.split()
    if len(tokens) <= 3:
        return None

    resolved_name, _ = resolve_medicine_name(q)
    if resolved_name:
        return resolved_name

    return None

def extract_last_context(history):
    context = {
        "medicine_name": None,
        "dci": None,
        "form": None,
        "dosage": None
    }

    if not history:
        return context

    for item in reversed(history):
        try:
            if isinstance(item, dict):
                user_msg = str(item.get("user", "") or "")
                bot_msg = str(item.get("assistant", "") or "")
                stored_med = item.get("medicine_name")
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                user_msg = str(item[0] or "")
                bot_msg = str(item[1] or "")
                stored_med = None
            else:
                continue

            if stored_med and not context["medicine_name"]:
                context["medicine_name"] = stored_med

            explicit_med = extract_explicit_medicine_from_query(user_msg)

            if explicit_med and not context["medicine_name"]:
                context["medicine_name"] = explicit_med

            if context["medicine_name"]:
                rows = get_rows_by_name(context["medicine_name"])
                if not rows.empty:
                    r = rows.iloc[0]
                    context["dci"] = r.get("DCI")
                    context["form"] = r.get("FORME")
                    context["dosage"] = r.get("DOSAGE_FULL")
                return context

        except Exception:
            continue

    return context

def row_to_context_block(row, rank=None):
    prefix = f"[Résultat {rank}]\n" if rank is not None else ""

    return f"""{prefix}
- Nom commercial : {row.get('NOM_COMMERCIAL', '')}
- DCI : {row.get('DCI', '')}
- Forme : {row.get('FORME', '')}
- Dosage : {row.get('DOSAGE_FULL', '')}
- Quantité : {row.get('QUANTITE_FULL', '')}
- Prix public : {format_price(row.get('PRIX_PUBLIC_NUM', ''))}
- Effets indésirables : {row.get('EFFETS_INDESIRABLES', '')}
""".strip()

def build_context_from_rows(rows, max_rows=5):
    """
    rows peut être :
    - un DataFrame
    - une liste de dicts
    """
    blocks = []

    if isinstance(rows, pd.DataFrame):
        if rows.empty:
            return ""
        sample = rows.head(max_rows).to_dict(orient="records")
    else:
        sample = rows[:max_rows] if rows else []

    for i, row in enumerate(sample, start=1):
        blocks.append(row_to_context_block(row, rank=i))

    return "\n\n---\n\n".join(blocks)

def looks_like_noise_query(query):
    q = normalize_text(query)
    tokens = q.split()

    if not tokens:
        return True

    generic_only = {
        "medicament", "medicaments", "médicament", "médicaments",
        "prix", "dosage", "forme", "dci", "compare", "comparer",
        "information", "informations", "info", "infos",
        "rouge", "bizarre", "truc", "random", "inconnu"
    }

    # médicament explicite ou comparaison => pas du bruit
    if extract_explicit_medicine_from_query(query) is not None:
        return False

    med1, med2 = extract_compare_medicines(query)
    if med1 and med2:
        return False

    # forme explicite => pas du bruit
    if detect_requested_form(query):
        return False

    # recherche alternative moins chère => pas du bruit
    if is_cheaper_alternative_query(query):
        return False

    # pays seul ne suffit pas
    meaningful_tokens = [t for t in tokens if t not in generic_only]

    # si aucun vrai token utile
    if len(meaningful_tokens) == 0:
        return True

    # si présence de token alphanumérique bizarre
    for t in tokens:
        if re.search(r"[a-zA-Z]", t) and re.search(r"\d", t):
            return True

    return False

def retrieve_structured_data(query, history=None, top_k=5):
    """
    Retourne un dictionnaire structuré contenant :
    - status
    - source_type
    - rows
    - medicine_name
    """
    memory = extract_last_context(history or [])
    explicit_med = extract_explicit_medicine_from_query(query)

    # 1) cas médicament explicite
    if explicit_med:
        rows = get_rows_by_name(explicit_med)
        if not rows.empty:
            return {
                "status": "ok",
                "source_type": "exact_medicine",
                "rows": rows.to_dict(orient="records"),
                "medicine_name": explicit_med
            }

    # 2) si on a un médicament en mémoire
    if not explicit_med and memory.get("medicine_name"):
        rows = get_rows_by_name(memory["medicine_name"])
        if not rows.empty:
            return {
                "status": "ok",
                "source_type": "memory_medicine",
                "rows": rows.to_dict(orient="records"),
                "medicine_name": memory["medicine_name"]
            }

    # 3) bruit
    if looks_like_noise_query(query):
        return {
            "status": "not_found",
            "source_type": None,
            "rows": [],
            "medicine_name": None
        }

    # 4) fallback sémantique avec garde-fou
    retrieved = semantic_search(query, top_k=top_k)

    if retrieved:
        # sécurité : on n'accepte pas un résultat sémantique
        # si aucun médicament réel n'est identifiable dans la requête
        if extract_explicit_medicine_from_query(query) is None:
            return {
                "status": "not_found",
                "source_type": None,
                "rows": [],
                "medicine_name": None
            }

        return {
            "status": "ok",
            "source_type": "semantic_search",
            "rows": retrieved,
            "medicine_name": None
        }

    return {
        "status": "not_found",
        "source_type": None,
        "rows": [],
        "medicine_name": None
    }

def has_suspicious_token(query):
    q = normalize_text(query)
    tokens = q.split()

    for t in tokens:
        # mélange lettres + chiffres
        if re.search(r"[a-zA-Z]", t) and re.search(r"\d", t):
            return True

        # mot long inconnu, non reconnu dans le vocabulaire
        if len(t) >= 5:
            if t not in medicine_names_normalized and t not in COMMON_WORDS:
                # on ignore les mots usuels déjà corrigés
                if t not in medicine_norm_to_original:
                    return True

    return False

def build_llm_prompt(task_type, user_query, context):
    if task_type == "compare":
        return f"""
Tu es un assistant spécialisé pour un délégué médical.

Réponds uniquement à partir du CONTEXTE fourni.
Ne rajoute aucune information absente du contexte.

Objectif :
- comparer les deux médicaments de manière claire et synthétique
- commencer par les points communs
- puis indiquer les différences visibles
- terminer par une conclusion simple

Règles :
- Réponds en français
- Sois professionnel, naturel et concis
- Ne donne aucun conseil thérapeutique
- Mentionne seulement ce qui apparaît dans le contexte
- Si des effets indésirables sont présents dans le contexte, mentionne-les clairement.
- Ne jamais inventer d’effets indésirables absents du contexte.
- Pour les questions sur les effets indésirables, réponds de façon ciblée.
- Ajoute une formulation prudente et informative.

CONTEXTE :
{context}

QUESTION UTILISATEUR :
{user_query}
""".strip()

    if task_type == "cheaper_alternative":
        return f"""
Tu es un assistant spécialisé pour un délégué médical.

Réponds uniquement à partir du CONTEXTE fourni.
Ne rajoute aucune information absente du contexte.

Objectif :
- expliquer quel est le médicament de référence
- présenter les alternatives moins chères
- mettre en avant les prix
- être clair et utile

Règles :
- Réponds en français
- Sois professionnel, naturel et concis
- Ne donne aucun conseil thérapeutique
- Si plusieurs alternatives existent, présente-les sous forme claire

CONTEXTE :
{context}

QUESTION UTILISATEUR :
{user_query}
""".strip()

    return f"""
Tu es un assistant spécialisé pour un délégué médical.

Tu dois répondre UNIQUEMENT à partir du CONTEXTE fourni.
Ne rajoute aucune information absente du contexte.
Ne t'appuie jamais sur tes connaissances générales.

Objectif :
- répondre clairement à la question
- si plusieurs variantes existent, les signaler explicitement
- pour une demande générale sur un médicament, résumer les principales variantes visibles
- rester fidèle au dataset

Règles :
- Réponds en français
- Sois naturel, professionnel et clair
- Ne donne aucun conseil thérapeutique
- Ne fais aucune supposition
- Ne réponds "Information non disponible dans le dataset." QUE si le contexte ne contient réellement pas l'information demandée

CONTEXTE :
{context}

QUESTION UTILISATEUR :
{user_query}
""".strip()

def generate_answer_with_llm(task_type, user_query, context, max_retries=1):
    prompt = build_llm_prompt(task_type, user_query, context)
    last_error = None

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            if hasattr(response, "text") and response.text:
                return response.text.strip()

            return None

        except Exception as e:
            last_error = e
            error_text = str(e).lower()

            if "503" in error_text or "unavailable" in error_text or "high demand" in error_text:
                wait_time = attempt + 1
                print(f"[Retry] Modèle indisponible, nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
                continue

            return None

    print(f"[LLM ERROR] {last_error}")
    return None

def fallback_single_medicine_response(rows, user_query="", intent="general"):
    if not rows:
        return "Je n’ai trouvé aucune information correspondante dans le dataset."

    if isinstance(rows, pd.DataFrame):
        rows = rows.to_dict(orient="records")

    if not rows:
        return "Je n’ai trouvé aucune information correspondante dans le dataset."

    first = rows[0]

    nom = first.get("NOM_COMMERCIAL", "Non disponible")
    dci = first.get("DCI", "Non disponible")
    query_lower = normalize_text(user_query)

    # --- effets indésirables ---
    if intent == "side_effects" or "effet" in query_lower or "indesirable" in query_lower or "indésirable" in query_lower or "secondaire" in query_lower:
        effects = first.get("EFFETS_INDESIRABLES", "")
        if effects and str(effects).strip():
            return f"Les effets indésirables de {nom} mentionnés dans le dataset sont : {effects}."
        return f"Je n’ai pas trouvé d’informations sur les effets indésirables de {nom} dans le dataset."

    # --- prix ---
    if intent == "price" or "prix" in query_lower or "tarif" in query_lower or "coute" in query_lower:
        lines = [f"Voici les prix disponibles pour {nom} dans le dataset :", ""]

        for row in rows[:5]:
            lines.append(
                f"- Forme : {row.get('FORME', '')} | "
                f"Dosage : {row.get('DOSAGE_FULL', '')} | "
                f"Quantité : {row.get('QUANTITE_FULL', '')} | "
                f"Prix public : {format_price(row.get('PRIX_PUBLIC_NUM', ''))}"
            )

        return "\n".join(lines)

    # --- dosage ---
    if intent == "dosage" or "dosage" in query_lower:
        seen = set()
        dosages = []

        for row in rows:
            dosage = str(row.get("DOSAGE_FULL", "")).strip()
            if dosage and dosage not in seen:
                seen.add(dosage)
                dosages.append(dosage)

        if not dosages:
            return f"Je n’ai pas trouvé de dosage exploitable pour {nom} dans le dataset."

        return f"Les dosages disponibles pour {nom} sont : " + ", ".join(dosages) + "."

    # --- forme ---
    if intent == "form" or "forme" in query_lower:
        seen = set()
        forms = []

        for row in rows:
            form = str(row.get("FORME", "")).strip()
            if form and form not in seen:
                seen.add(form)
                forms.append(form)

        if not forms:
            return f"Je n’ai pas trouvé de forme exploitable pour {nom} dans le dataset."

        return f"Les formes disponibles pour {nom} sont : " + ", ".join(forms) + "."

    # --- DCI ---
    if intent == "dci" or "principe actif" in query_lower or "dci" in query_lower:
        return f"La DCI de {nom} est {dci}."

    # --- info générale ---
    lines = [f"Voici les informations disponibles concernant {nom} dans le dataset :"]

    if dci and dci != "Non disponible":
        lines.append(f"DCI : {dci}")

    effects = first.get("EFFETS_INDESIRABLES", "")
    if effects and str(effects).strip():
        lines.append(f"Effets indésirables : {effects}")

    lines.append("")
    lines.append("Plusieurs variantes sont disponibles :")

    for row in rows[:5]:
        lines.append(
            f"- Forme : {row.get('FORME', '')} | "
            f"Dosage : {row.get('DOSAGE_FULL', '')} | "
            f"Quantité : {row.get('QUANTITE_FULL', '')} | "
            f"Prix public : {format_price(row.get('PRIX_PUBLIC_NUM', ''))}"
        )

    return "\n".join(lines)

def fallback_compare_response(name1, name2):
    n1, _ = resolve_medicine_name(name1)
    n2, _ = resolve_medicine_name(name2)

    if not n1 or not n2:
        return "Je n’ai pas pu identifier clairement les deux médicaments à comparer dans le dataset."

    r1 = get_rows_by_name(n1)
    r2 = get_rows_by_name(n2)

    if r1.empty or r2.empty:
        return "Je n’ai pas trouvé suffisamment d’informations dans le dataset pour comparer ces deux médicaments."

    a = r1.iloc[0].to_dict()
    b = r2.iloc[0].to_dict()

    nom1 = a.get("NOM_COMMERCIAL", n1)
    nom2 = b.get("NOM_COMMERCIAL", n2)

    dci1 = a.get("DCI", "Non disponible")
    dci2 = b.get("DCI", "Non disponible")

    forme1 = a.get("FORME", "Non disponible")
    forme2 = b.get("FORME", "Non disponible")

    dosage1 = a.get("DOSAGE_FULL", "Non disponible")
    dosage2 = b.get("DOSAGE_FULL", "Non disponible")

    quantite1 = a.get("QUANTITE_FULL", "Non disponible")
    quantite2 = b.get("QUANTITE_FULL", "Non disponible")

    prix1 = a.get("PRIX_PUBLIC_NUM", "")
    prix2 = b.get("PRIX_PUBLIC_NUM", "")

    texte = []
    texte.append(f"Comparaison entre {nom1} et {nom2} :")
    texte.append(f"- DCI : {nom1} = {dci1} | {nom2} = {dci2}")
    texte.append(f"- Forme : {nom1} = {forme1} | {nom2} = {forme2}")
    texte.append(f"- Dosage : {nom1} = {dosage1} | {nom2} = {dosage2}")
    texte.append(f"- Quantité : {nom1} = {quantite1} | {nom2} = {quantite2}")
    texte.append(f"- Prix public : {nom1} = {format_price(prix1)} | {nom2} = {format_price(prix2)}")

    try:
        p1 = float(prix1)
        p2 = float(prix2)

        if p1 < p2:
            texte.append(f"{nom1} est moins cher que {nom2}.")
        elif p2 < p1:
            texte.append(f"{nom2} est moins cher que {nom1}.")
        else:
            texte.append(f"{nom1} et {nom2} ont le même prix public.")
    except:
        pass

    return "\n".join(texte)

def detect_geographic_constraint(query):
    q = normalize_text(query)

    countries = [
        "allemagne", "france", "tunisie", "maroc", "algerie",
        "usa", "canada", "europe", "italie", "espagne"
    ]

    for country in countries:
        if country in q:
            return country

    return None

def is_cheaper_alternative_query(query):
    q = normalize_text(query)

    patterns = [
        "alternative moins chere",
        "alternative moins cher",
        "moins chere que",
        "moins cher que",
        "equivalent moins cher",
        "equivalent moins chere",
        "medicament moins cher",
        "un moins cher",
        "une alternative"
    ]

    return any(p in q for p in patterns)

def detect_requested_form(query):
    q = normalize_text(query)

    form_map = {
        "comprime": "COMPRIME",
        "comprimes": "COMPRIME",
        "comprimé": "COMPRIME",
        "comprimés": "COMPRIME",
        "sirop": "SIROP",
        "gelule": "GELULE",
        "gelules": "GELULE",
        "gélule": "GELULE",
        "gélules": "GELULE",
        "collyre": "COLLYRE",
        "creme": "CREME",
        "crème": "CREME",
        "poudre": "POUDRE",
        "solution": "SOLUTION",
        "suspension": "SUSPENSION"
    }

    for key, value in form_map.items():
        if key in q:
            return value

    return None

def is_generic_form_query(query):
    q = normalize_text(query)

    generic_patterns = [
        "donne moi un medicament en",
        "donne moi des medicaments en",
        "montre moi un medicament en",
        "montre moi des medicaments en",
        "je veux un medicament en",
        "je veux des medicaments en",
        "medicament en",
        "medicaments en"
    ]

    requested_form = detect_requested_form(query)

    return requested_form is not None and any(p in q for p in generic_patterns)

def retrieve_distinct_medicines_by_form(form_value, top_n=5):
    if not form_value:
        return []

    filtered = df[
        df["FORME"].fillna("").astype(str).str.upper().str.contains(form_value, regex=False)
    ].copy()

    if filtered.empty:
        return []

    # garder de préférence les lignes avec prix
    if "PRIX_PUBLIC_NUM" in filtered.columns:
        filtered = filtered.sort_values(by="PRIX_PUBLIC_NUM", ascending=True, na_position="last")

    # déduplication par NOM_COMMERCIAL
    distinct_rows = []
    seen_names = set()

    for _, row in filtered.iterrows():
        name = str(row.get("NOM_COMMERCIAL", "")).strip().upper()
        if not name:
            continue

        if name not in seen_names:
            seen_names.add(name)
            distinct_rows.append(row.to_dict())

        if len(distinct_rows) >= top_n:
            break

    return distinct_rows

def build_form_search_context(form_value, rows):
    if not rows:
        return None

    blocks = [f"[Recherche par forme]\nForme demandée: {form_value}"]

    for i, row in enumerate(rows, start=1):
        blocks.append(
            f"""[Médicament {i}]
Nom commercial: {row.get('NOM_COMMERCIAL', '')}
DCI: {row.get('DCI', '')}
Forme: {row.get('FORME', '')}
Dosage: {row.get('DOSAGE_FULL', '')}
Quantité: {row.get('QUANTITE_FULL', '')}
Prix public: {row.get('PRIX_PUBLIC_NUM', '')}"""
        )

    return "\n\n---\n\n".join(blocks)

def fallback_form_search_response(form_value, rows):
    if not rows:
        return f"Je n’ai trouvé aucun médicament sous la forme {form_value.lower()} dans le dataset."

    lines = [f"Voici quelques médicaments sous forme de {form_value.lower()} dans le dataset :", ""]

    for row in rows:
        lines.append(
            f"- {row.get('NOM_COMMERCIAL', '')} | "
            f"DCI : {row.get('DCI', '')} | "
            f"Dosage : {row.get('DOSAGE_FULL', '')} | "
            f"Prix public : {format_price(row.get('PRIX_PUBLIC_NUM', ''))}"
        )

    return "\n".join(lines)

def detect_intent_from_query(query):
    q = normalize_text(query)

    if is_cheaper_alternative_query(q):
        return "cheaper_alternative"


    if is_safer_alternative_query(q):
        return "safer_alternative"

    med1, med2 = extract_compare_medicines(q)
    if med1 and med2:
        return "compare"

    if is_generic_form_query(q):
        return "form_search"


    if "effet" in q or "effets" in q or "indesirable" in q or "indésirable" in q or "secondaire" in q or "secondaires" in q:
       return "side_effects"

    if "prix" in q or "coute" in q or "coûte" in q or "tarif" in q:
        return "price"

    if "dosage" in q:
        return "dosage"

    if "forme" in q or "formes" in q:
        return "form"

    if "dci" in q or "principe actif" in q:
        return "dci"

    if "info" in q or "infos" in q or "information" in q or "parle" in q:
        return "medicine_info"

    return "general"


def is_followup_query(query):
    q = normalize_text(query)

    followup_markers = [
        "son prix", "son dosage", "sa forme", "sa dci",
        "quel est son prix", "et son prix", "et son dosage",
        "quel est son dosage", "et sa forme", "et sa dci"
    ]

    return any(marker in q for marker in followup_markers)


def is_safer_alternative_query(query):
    q = normalize_text(query)

    patterns = [
        "moins d effets indesirables",
        "moins d'effets indesirables",
        "moins d effets indésirables",
        "moins d'effets indésirables",
        "moins d effets secondaires",
        "moins d'effets secondaires",
        "mieux tolere",
        "mieux toléré",
        "plus sur",
        "plus sûr",
        "moins de risque"
    ]

    return any(p in q for p in patterns)


def analyze_query(query, history=None):
    normalized_query = normalize_user_query(query)
    corrected_query = correct_query_with_symspell(normalized_query)

    memory = extract_last_context(history or [])

    med1, med2 = extract_compare_medicines(corrected_query)
    explicit_medicine = extract_explicit_medicine_from_query(corrected_query)
    requested_form = detect_requested_form(corrected_query)
    country = detect_geographic_constraint(corrected_query)
    intent = detect_intent_from_query(corrected_query)
    is_followup = is_followup_query(corrected_query)

    # fallback mémoire uniquement pour les vraies questions de suivi
    if not explicit_medicine and memory.get("medicine_name"):
        if is_followup:
            explicit_medicine = memory.get("medicine_name")

    analysis = {
        "raw_query": query,
        "normalized_query": normalized_query,
        "corrected_query": corrected_query,
        "intent": intent,
        "medicine_name": explicit_medicine,
        "medicine_name_2": med2 if med1 and med2 else None,
        "compare_pair": (med1, med2) if med1 and med2 else None,
        "form": requested_form,
        "country": country,
        "is_compare": med1 is not None and med2 is not None,
        "is_cheaper_alternative": is_cheaper_alternative_query(corrected_query),
        "is_form_search": is_generic_form_query(corrected_query),
        "is_noise": looks_like_noise_query(corrected_query),
        "is_followup": is_followup,
        "memory": memory
    }

    return analysis

import unicodedata

# =========================================================
# SCORING V2 DES EFFETS INDESIRABLES
# Objectif :
# - même DCI
# - comparer la "lourdeur" du texte des effets indésirables
# - NE PAS utiliser la forme comme critère
# =========================================================

EFFECT_LEXICON = {
    "light": {
        "irritation": [r"\birritation(?:s)?\b", r"\birritation locale\b"],
        "brulure": [r"\bbrulure(?:s)?\b"],
        "picotement": [r"\bpicotement(?:s)?\b"],
        "secheresse": [r"\bsecheresse\b", r"\bsecheresse buccale\b"],
        "rougeur": [r"\brougeur(?:s)?\b", r"\berytheme\b"],
        "gout_desagreable": [r"\bgout amer\b", r"\bgout desagreable\b"]
    },

    "moderate": {
        "nausee": [r"\bnausee(?:s)?\b"],
        "vomissement": [r"\bvomissement(?:s)?\b"],
        "constipation": [r"\bconstipation\b"],
        "diarrhee": [r"\bdiarrhee(?:s)?\b"],
        "douleur_abdominale": [r"\bdouleur(?:s)? abdominale(?:s)?\b"],
        "trouble_digestif": [r"\btrouble(?:s)? digestif(?:s)?\b"],
        "eruption_cutanee": [r"\beruption cutanee\b", r"\brush\b"],
        "prurit": [r"\bprurit\b", r"\bdemangeaison(?:s)?\b"],
        "fatigue": [r"\bfatigue\b", r"\basthenie\b"],
        "cephalee": [r"\bcephalee(?:s)?\b", r"\bmaux? de tete\b"],
        "vertige": [r"\bvertige(?:s)?\b"],
        "somnolence": [r"\bsomnolence\b"],
        "douleur": [r"\bdouleur(?:s)?\b"]
    },

    "severe": {
        "oedeme": [r"\boedeme(?:s)?\b"],
        "hypotension": [r"\bhypotension\b"],
        "hypertension": [r"\bhypertension\b"],
        "tachycardie": [r"\btachycardie\b", r"\bpalpitation(?:s)?\b"],
        "dyspnee": [r"\bdyspnee\b", r"\bdetresse respiratoire\b"],
        "allergie": [r"\ballergie(?:s)?\b", r"\breaction allergique\b"],
        "hepatique": [r"\batteinte hepatique\b", r"\bhepatite\b"],
        "ulcere": [r"\bulcere(?:s)?\b"],
        "hemorragie": [r"\bhemorragie(?:s)?\b"],
        "convulsion": [r"\bconvulsion(?:s)?\b"]
    }
}

TERM_WEIGHTS = {
    "light": 1.0,
    "moderate": 2.5,
    "severe": 5.0
}

TERM_SYSTEM = {
    "irritation": "cutane",
    "brulure": "cutane",
    "picotement": "cutane",
    "secheresse": "cutane",
    "rougeur": "cutane",
    "eruption_cutanee": "cutane",
    "prurit": "cutane",
    "oedeme": "cutane",

    "nausee": "digestif",
    "vomissement": "digestif",
    "constipation": "digestif",
    "diarrhee": "digestif",
    "douleur_abdominale": "digestif",
    "trouble_digestif": "digestif",
    "ulcere": "digestif",
    "hemorragie": "digestif",

    "fatigue": "general",
    "gout_desagreable": "general",
    "douleur": "general",

    "cephalee": "neurologique",
    "vertige": "neurologique",
    "somnolence": "neurologique",
    "convulsion": "neurologique",

    "hypotension": "cardiovasculaire",
    "hypertension": "cardiovasculaire",
    "tachycardie": "cardiovasculaire",

    "dyspnee": "respiratoire",
    "allergie": "immunologique",
    "hepatique": "hepatique"
}

LIGHT_CONTEXT_PATTERNS = [
    r"\bleger(?:e|es|s)?\b",
    r"\btransitoire(?:s)?\b",
    r"\brare(?:ment)?\b",
    r"\bpeu frequent(?:e|es|s)?\b",
    r"\blocal(?:e|es|s)?\b",
    r"\bbenin(?:e|es|s)?\b"
]

HEAVY_CONTEXT_PATTERNS = [
    r"\bsevere(?:s)?\b",
    r"\bgrave(?:s)?\b",
    r"\bimportant(?:e|es|s)?\b",
    r"\bfrequent(?:e|es|s)?\b",
    r"\bpersistant(?:e|es|s)?\b",
    r"\burgence\b",
    r"\bhospitalisation\b",
    r"\bchoc\b",
    r"\bdetresse\b"
]


def normalize_side_effect_text(text, preserve_separators=False):
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""

    text = str(text).lower()

    # ligatures importantes
    text = text.replace("œ", "oe").replace("æ", "ae")

    # suppression accents
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # si on veut préserver les séparateurs pour le split
    if preserve_separators:
        text = re.sub(r"[•;]+", "\n", text)
        text = re.sub(r"[(){}\[\]]", " ", text)
        text = re.sub(r"[-–—]", " ", text)
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    text = re.sub(r"[(){}\[\]/]", " ", text)
    text = re.sub(r"[-–—]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def split_side_effect_items(text):
    if not text:
        return []

    # On garde les séparateurs avant nettoyage complet
    normalized = normalize_side_effect_text(text, preserve_separators=True)

    # découpe par retour ligne, virgule ou point-virgule
    parts = re.split(r"[\n,;]+", normalized)

    cleaned = []
    for part in parts:
        item = re.sub(r"\s+", " ", str(part)).strip(" .:-")
        if item:
            cleaned.append(item)

    return cleaned


def extract_effect_hits_from_item(item_text):
    hits = []

    for severity, terms in EFFECT_LEXICON.items():
        for term_name, patterns in terms.items():
            if any(re.search(pattern, item_text) for pattern in patterns):
                hits.append((term_name, severity))

    # déduplication locale
    deduped = []
    seen = set()
    for term_name, severity in hits:
        if term_name not in seen:
            seen.add(term_name)
            deduped.append((term_name, severity))

    return deduped


def compute_side_effect_profile(effects_text, form=None):
    """
    form est conservé uniquement pour compatibilité avec le reste du notebook,
    mais n'est PAS utilisé dans le score.
    """
    if effects_text is None or (isinstance(effects_text, float) and pd.isna(effects_text)):
        return None

    items = split_side_effect_items(effects_text)

    if not items:
        fallback_text = normalize_side_effect_text(effects_text, preserve_separators=False)
        if not fallback_text:
            return None
        items = [fallback_text]

    total_score = 0.0
    matched_terms = []
    matched_systems = set()
    unknown_item_count = 0

    for item in items:
        local_hits = extract_effect_hits_from_item(item)
        item_score = 0.0

        if local_hits:
            for term_name, severity in local_hits:
                item_score += TERM_WEIGHTS[severity]
                matched_terms.append((term_name, severity))
                matched_systems.add(TERM_SYSTEM.get(term_name, "autre"))
        else:
            unknown_item_count += 1
            item_score += 0.75

        if any(re.search(p, item) for p in LIGHT_CONTEXT_PATTERNS):
            item_score *= 0.75

        if any(re.search(p, item) for p in HEAVY_CONTEXT_PATTERNS):
            item_score *= 1.50

        total_score += item_score

    # Déduplication globale des termes reconnus
    unique_terms = []
    seen_terms = set()
    for term_name, severity in matched_terms:
        if term_name not in seen_terms:
            seen_terms.add(term_name)
            unique_terms.append((term_name, severity))

    # Bonus de diversité des systèmes touchés
    total_score += max(len(matched_systems) - 1, 0) * 0.60

    total_score = round(total_score, 2)

    return {
        "score": total_score,
        "normalized_text": normalize_side_effect_text(effects_text, preserve_separators=False),
        "items": items,
        "matched_terms": unique_terms,
        "matched_systems": sorted(matched_systems),
        "unknown_item_count": unknown_item_count,
        "known_effect_count": len(unique_terms),
        "effect_item_count": len(items)
    }


def compute_side_effect_score(effects_text, form=None):
    profile = compute_side_effect_profile(effects_text, form=form)
    if profile is None:
        return None
    return profile["score"]


def summarize_profile_hits(profile, max_terms=6):
    if not profile:
        return "Non disponible"

    labels = {
        "irritation": "irritation",
        "brulure": "brûlure",
        "picotement": "picotements",
        "secheresse": "sécheresse",
        "rougeur": "rougeur",
        "gout_desagreable": "goût désagréable",
        "nausee": "nausée",
        "vomissement": "vomissements",
        "constipation": "constipation",
        "diarrhee": "diarrhée",
        "douleur_abdominale": "douleur abdominale",
        "trouble_digestif": "troubles digestifs",
        "eruption_cutanee": "éruption cutanée",
        "prurit": "prurit",
        "fatigue": "fatigue/asthénie",
        "cephalee": "céphalées",
        "vertige": "vertiges",
        "somnolence": "somnolence",
        "douleur": "douleurs",
        "oedeme": "œdèmes",
        "hypotension": "hypotension",
        "hypertension": "hypertension",
        "tachycardie": "tachycardie/palpitations",
        "dyspnee": "dyspnée",
        "allergie": "allergie",
        "hepatique": "atteinte hépatique",
        "ulcere": "ulcère",
        "hemorragie": "hémorragie",
        "convulsion": "convulsions"
    }

    terms = [labels.get(term_name, term_name) for term_name, _ in profile.get("matched_terms", [])]
    if not terms:
        return "Effets non classés précisément"

    return ", ".join(terms[:max_terms])

response_cache = {}


def get_disclaimer():
    return (
        "⚠️ Cet assistant répond uniquement à partir du dataset.\n"
        "⚠️ Les informations médicales, y compris les effets indésirables, sont fournies à titre informatif uniquement.\n\n"
    )


def format_price(value):
    """
    Formate les prix en dinars tunisiens.
    Exemple:
    1.815 -> 1.815 DT
    2 -> 2.000 DT
    None -> Non disponible
    """
    try:
        if value is None or value == "":
            return "Non disponible"

        val = float(value)
        return f"{val:.3f} DT"

    except:
        return f"{value} DT"


def should_use_cache(query):
    return len(query.split()) >= 3


def get_cached_response(query):
    return response_cache.get(query)


def save_cached_response(query, response):
    response_cache[query] = response
    return response


def is_valid_llm_answer(answer):
    if not answer:
        return False

    normalized = answer.strip().lower()
    if normalized == "information non disponible dans le dataset.":
        return False

    return True


def apply_global_guardrails(message, query, history):
    disclaimer = get_disclaimer()

    country = detect_geographic_constraint(query)

    if country and country != "tunisie":
        retrieval = retrieve_structured_data(query, history=history, top_k=5)

        if retrieval["status"] == "ok":
            context = build_context_from_rows(retrieval["rows"], max_rows=1)
            answer = generate_answer_with_llm("general", message, context)

            return disclaimer + (
                "Les informations de ce chatbot sont basées sur un dataset provenant de la Tunisie. "
                f"Ce dataset ne contient pas de données spécifiques à d'autres pays comme {country}.\n\n"
                "Cependant, voici les informations disponibles dans le dataset :\n\n"
                + (
                    answer
                    if is_valid_llm_answer(answer)
                    else fallback_single_medicine_response(retrieval["rows"], user_query=message)
                )
            )

        return disclaimer + (
            "Les informations de ce chatbot sont basées sur un dataset provenant de la Tunisie. "
            f"Ce dataset ne contient pas de données spécifiques à d'autres pays comme {country}, "
            "et je n’ai trouvé aucune information correspondante."
        )

    return None


def handle_cheaper_alternative(message, query):
    disclaimer = get_disclaimer()

    alt_result = find_cheaper_alternatives_structured(query, top_n=5)
    alt_context = build_cheaper_alternative_context(alt_result)

    if alt_context:
        answer = generate_answer_with_llm("cheaper_alternative", message, alt_context)
        if is_valid_llm_answer(answer):
            return disclaimer + answer

    return disclaimer + fallback_cheaper_alternative_response(alt_result)


def format_safer_alternative_response_premium(base_name, base_dci, base_score, base_summary, alternatives):
    lines = []

    lines.append(
        f"Voici les alternatives les mieux classées à {base_name}, avec la même DCI ({base_dci}) "
        "et un profil d’effets indésirables estimé plus léger dans le dataset :"
    )
    lines.append("")
    lines.append(
        f"{base_name} a un score estimé de {base_score} avec les effets détectés suivants : {base_summary}."
    )
    lines.append(
        "Les alternatives ci-dessous ont un score plus faible car leur profil d’effets indésirables paraît moins chargé dans le dataset."
    )
    lines.append("")

    for i, alt in enumerate(alternatives, start=1):
        alt_name = alt.get("NOM_COMMERCIAL", "")
        alt_form = alt.get("FORME", "")
        alt_dosage = alt.get("DOSAGE_FULL", "")
        alt_price = alt.get("PRIX_PUBLIC_NUM", "")
        alt_score = alt.get("SIDE_EFFECT_SCORE", "")
        alt_gap = alt.get("SCORE_GAP", "")
        alt_summary = alt.get("SIDE_EFFECT_SUMMARY", "Non disponible")

        lines.append(f"{i}. {alt_name}")
        lines.append(f"   Forme : {alt_form}")
        lines.append(f"   Dosage : {alt_dosage}")
        lines.append(f"   Prix public : {format_price(alt_price)}")
        lines.append(f"   Score estimé : {alt_score}")
        lines.append(f"   Gain estimé : {alt_gap}")
        lines.append(f"   Effets détectés : {alt_summary}")
        lines.append(
            f"   Interprétation : le profil détecté de {alt_name} paraît plus léger que celui de {base_name} dans le dataset."
        )
        lines.append("")

    lines.append(
        f"En résumé, {alternatives[0].get('NOM_COMMERCIAL', 'cette alternative')} apparaît comme l’option la plus légère parmi les médicaments de même DCI présents dans le dataset."
    )
    lines.append("")
    lines.append(
        "⚠️ Cette comparaison est basée uniquement sur l’analyse textuelle des effets indésirables présents dans le dataset. "
        "Elle sert à comparer la lourdeur apparente des profils décrits, et ne constitue pas un avis médical."
    )

    return "\n".join(lines)


def handle_safer_alternative(message, query):
    disclaimer = get_disclaimer()

    result = find_safer_alternatives_structured(query, top_n=3)

    if result["status"] != "ok":
        return disclaimer + "Je n’ai pas pu identifier correctement le médicament de référence dans le dataset."

    base = result["base_row"]
    base_profile = result.get("base_profile")
    alternatives = result["alternatives"]
    reason = result.get("reason")

    base_name = base.get("NOM_COMMERCIAL", "ce médicament")
    base_dci = base.get("DCI", "")
    base_score = base_profile["score"] if base_profile else None
    base_summary = summarize_profile_hits(base_profile)

    if not alternatives:
        if reason == "same_or_higher_scores":
            return disclaimer + (
                f"Je n’ai pas trouvé d’alternative à {base_name} avec la même DCI ({base_dci}) "
                "et un score d’effets indésirables estimé plus faible dans le dataset.\n\n"
                f"{base_name} présente dans le dataset les effets suivants : {base_summary}.\n"
                "Les autres médicaments de même DCI ont des profils identiques, proches, ou plus lourds."
            )

        return disclaimer + (
            f"Je n’ai pas trouvé d’alternative avec moins d’effets indésirables que {base_name} dans le dataset."
        )

    premium_body = format_safer_alternative_response_premium(
        base_name=base_name,
        base_dci=base_dci,
        base_score=base_score,
        base_summary=base_summary,
        alternatives=alternatives
    )

    return disclaimer + premium_body


def handle_compare(message, query):
    disclaimer = get_disclaimer()

    med1, med2 = extract_compare_medicines(query)
    if not (med1 and med2):
        return disclaimer + "Je n’ai pas pu identifier clairement les deux médicaments à comparer."

    compare_context = build_compare_context(med1, med2)
    if compare_context:
        answer = generate_answer_with_llm("compare", message, compare_context)
        if is_valid_llm_answer(answer):
            return disclaimer + answer

    return disclaimer + fallback_compare_response(med1, med2)


def handle_form_query(message, query):
    disclaimer = get_disclaimer()

    form_value = detect_requested_form(query)
    if not form_value:
        return disclaimer + "Je n’ai pas pu identifier la forme demandée dans le dataset."

    rows = retrieve_distinct_medicines_by_form(form_value, top_n=5)
    if not rows:
        return disclaimer + f"Je n’ai trouvé aucun médicament sous forme de {form_value.lower()} dans le dataset."

    context = build_form_search_context(form_value, rows)
    if context:
        answer = generate_answer_with_llm("general", message, context)
        if is_valid_llm_answer(answer):
            return disclaimer + answer

    return disclaimer + fallback_form_search_response(form_value, rows)


def handle_general_query(message, query, history, analysis=None):
    disclaimer = get_disclaimer()

    retrieval = retrieve_structured_data(query, history=history, top_k=5)

    if retrieval["status"] != "ok":
        return disclaimer + "Je n’ai trouvé aucune information correspondante dans le dataset."

    context = build_context_from_rows(retrieval["rows"], max_rows=5)

    if not context.strip():
        return disclaimer + "Je n’ai trouvé aucune information exploitable dans le dataset."

    answer = generate_answer_with_llm("general", message, context)

    if is_valid_llm_answer(answer):
        return disclaimer + answer

    intent = analysis["intent"] if analysis else "general"

    return disclaimer + fallback_single_medicine_response(
        retrieval["rows"],
        user_query=message,
        intent=intent
    )


def chatbot_response_hybrid(message, history):
    analysis = analyze_query(message, history)
    query = analysis["corrected_query"]
    use_cache = should_use_cache(query)

    if use_cache:
        cached = get_cached_response(query)
        if cached:
            return cached

    if analysis["is_noise"]:
        response = get_disclaimer() + "Je n’ai trouvé aucune information correspondante dans le dataset."
        if use_cache:
            return save_cached_response(query, response)
        return response

    guardrail_response = apply_global_guardrails(message, query, history)
    if guardrail_response:
        if use_cache:
            return save_cached_response(query, guardrail_response)
        return guardrail_response

    if analysis["is_cheaper_alternative"]:
        response = handle_cheaper_alternative(message, query)
        if response is None:
            response = get_disclaimer() + "Je n’ai trouvé aucune information correspondante dans le dataset."
        if use_cache:
            return save_cached_response(query, response)
        return response

    if analysis["intent"] == "safer_alternative":
        response = handle_safer_alternative(message, query)
        if response is None:
            response = get_disclaimer() + "Je n’ai trouvé aucune information correspondante dans le dataset."
        if use_cache:
            return save_cached_response(query, response)
        return response

    if analysis["is_compare"]:
        response = handle_compare(message, query)
        if response is None:
            response = get_disclaimer() + "Je n’ai trouvé aucune information correspondante dans le dataset."
        if use_cache:
            return save_cached_response(query, response)
        return response

    if analysis["is_form_search"]:
        response = handle_form_query(message, query)
        if response is None:
            response = get_disclaimer() + "Je n’ai trouvé aucune information correspondante dans le dataset."
        if use_cache:
            return save_cached_response(query, response)
        return response

    response = handle_general_query(message, query, history, analysis=analysis)
    if response is None:
        response = get_disclaimer() + "Je n’ai trouvé aucune information correspondante dans le dataset."

    if use_cache:
        return save_cached_response(query, response)
    return response

def build_compare_context(name1, name2, max_rows=3):
    n1, _ = resolve_medicine_name(name1)
    n2, _ = resolve_medicine_name(name2)

    if not n1 or not n2:
        return None

    r1 = get_rows_by_name(n1)
    r2 = get_rows_by_name(n2)

    if r1.empty or r2.empty:
        return None

    rows1 = r1.head(max_rows).to_dict(orient="records")
    rows2 = r2.head(max_rows).to_dict(orient="records")

    blocks1 = []
    for i, row in enumerate(rows1, start=1):
        blocks1.append(
            f"""[Médicament 1 - Variante {i}]
Nom commercial: {row.get('NOM_COMMERCIAL', '')}
DCI: {row.get('DCI', '')}
Forme: {row.get('FORME', '')}
Dosage: {row.get('DOSAGE_FULL', '')}
Quantité: {row.get('QUANTITE_FULL', '')}
Prix public: {row.get('PRIX_PUBLIC_NUM', '')}"""
        )

    blocks2 = []
    for i, row in enumerate(rows2, start=1):
        blocks2.append(
            f"""[Médicament 2 - Variante {i}]
Nom commercial: {row.get('NOM_COMMERCIAL', '')}
DCI: {row.get('DCI', '')}
Forme: {row.get('FORME', '')}
Dosage: {row.get('DOSAGE_FULL', '')}
Quantité: {row.get('QUANTITE_FULL', '')}
Prix public: {row.get('PRIX_PUBLIC_NUM', '')}"""
        )

    context = "\n\n---\n\n".join(blocks1 + blocks2)
    return context

def find_cheaper_alternatives_structured(query, top_n=5):
    """
    Retourne les alternatives moins chères au médicament demandé.
    Compare sur la même DCI quand possible.
    """
    medicine_name = extract_explicit_medicine_from_query(query)

    if not medicine_name:
        resolved_name, _ = resolve_medicine_name(query)
        medicine_name = resolved_name

    if not medicine_name:
        return {
            "status": "not_found",
            "reason": "medicine_not_found",
            "base_medicine": None,
            "base_row": None,
            "alternatives": []
        }

    rows = get_rows_by_name(medicine_name)
    if rows.empty:
        return {
            "status": "not_found",
            "reason": "medicine_not_found",
            "base_medicine": medicine_name,
            "base_row": None,
            "alternatives": []
        }

    base_row = rows.iloc[0].to_dict()
    base_dci = str(base_row.get("DCI", "")).strip()
    base_price = base_row.get("PRIX_PUBLIC_NUM", None)

    try:
        base_price = float(base_price)
    except:
        return {
            "status": "not_found",
            "reason": "base_price_missing",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "alternatives": []
        }

    if not base_dci:
        return {
            "status": "not_found",
            "reason": "base_dci_missing",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "alternatives": []
        }

    candidates = df[
        df["DCI"].fillna("").astype(str).str.upper() == base_dci.upper()
    ].copy()

    if candidates.empty:
        return {
            "status": "not_found",
            "reason": "no_same_dci",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "alternatives": []
        }

    candidates = candidates[candidates["PRIX_PUBLIC_NUM"].notna()].copy()

    try:
        candidates["PRIX_PUBLIC_NUM"] = candidates["PRIX_PUBLIC_NUM"].astype(float)
    except:
        pass

    candidates = candidates[
        candidates["PRIX_PUBLIC_NUM"] < base_price
    ].copy()

    candidates = candidates[
        candidates["NOM_COMMERCIAL"].fillna("").astype(str).str.upper() != str(medicine_name).upper()
    ].copy()

    if candidates.empty:
        return {
            "status": "ok",
            "reason": "no_cheaper_alternative",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "alternatives": []
        }

    candidates = candidates.sort_values(by="PRIX_PUBLIC_NUM", ascending=True)

    # déduplication simple
    seen = set()
    cleaned = []

    for _, row in candidates.iterrows():
        item = row.to_dict()
        key = (
            str(item.get("NOM_COMMERCIAL", "")).upper(),
            str(item.get("DOSAGE_FULL", "")).upper(),
            str(item.get("FORME", "")).upper(),
            str(item.get("PRIX_PUBLIC_NUM", ""))
        )
        if key not in seen:
            seen.add(key)
            cleaned.append(item)

    return {
        "status": "ok",
        "reason": "found",
        "base_medicine": medicine_name,
        "base_row": base_row,
        "alternatives": cleaned[:top_n]
    }

def find_safer_alternatives_structured(query, top_n=3):
    medicine_name = extract_reference_medicine_for_safer_alternative(query)

    if not medicine_name:
        return {
            "status": "not_found",
            "reason": "medicine_not_found",
            "base_medicine": None,
            "base_row": None,
            "base_profile": None,
            "alternatives": []
        }

    rows = get_rows_by_name(medicine_name)
    if rows.empty:
        return {
            "status": "not_found",
            "reason": "medicine_not_found",
            "base_medicine": medicine_name,
            "base_row": None,
            "base_profile": None,
            "alternatives": []
        }

    base_row = rows.iloc[0].to_dict()
    base_dci = str(base_row.get("DCI", "")).strip()
    base_effects = base_row.get("EFFETS_INDESIRABLES", "")

    base_profile = compute_side_effect_profile(base_effects)
    if not base_dci:
        return {
            "status": "not_found",
            "reason": "base_dci_missing",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "base_profile": base_profile,
            "alternatives": []
        }

    if base_profile is None:
        return {
            "status": "not_found",
            "reason": "base_effects_missing",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "base_profile": None,
            "alternatives": []
        }

    base_score = base_profile["score"]

    candidates = df[
        df["DCI"].fillna("").astype(str).str.upper() == base_dci.upper()
    ].copy()

    candidates = candidates[
        candidates["NOM_COMMERCIAL"].fillna("").astype(str).str.upper() != str(medicine_name).upper()
    ].copy()

    if candidates.empty:
        return {
            "status": "ok",
            "reason": "no_safer_alternative",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "base_profile": base_profile,
            "alternatives": []
        }

    candidates["SIDE_EFFECT_PROFILE"] = candidates["EFFETS_INDESIRABLES"].apply(
        lambda x: compute_side_effect_profile(x)
    )

    candidates = candidates[candidates["SIDE_EFFECT_PROFILE"].notna()].copy()

    if candidates.empty:
        return {
            "status": "ok",
            "reason": "no_safer_alternative",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "base_profile": base_profile,
            "alternatives": []
        }

    candidates["SIDE_EFFECT_SCORE"] = candidates["SIDE_EFFECT_PROFILE"].apply(lambda p: p["score"])
    candidates["SCORE_GAP"] = candidates["SIDE_EFFECT_SCORE"].apply(lambda s: round(base_score - s, 2))

    # amélioration minimale pour éviter les différences trop faibles
    MIN_SCORE_IMPROVEMENT = 1.5
    candidates = candidates[candidates["SCORE_GAP"] >= MIN_SCORE_IMPROVEMENT].copy()

    if candidates.empty:
        same_dci_candidates = df[
            df["DCI"].fillna("").astype(str).str.upper() == base_dci.upper()
        ].copy()

        same_dci_candidates = same_dci_candidates[
            same_dci_candidates["NOM_COMMERCIAL"].fillna("").astype(str).str.upper() != str(medicine_name).upper()
        ].copy()

        if not same_dci_candidates.empty:
            same_dci_candidates["SIDE_EFFECT_PROFILE"] = same_dci_candidates["EFFETS_INDESIRABLES"].apply(
                lambda x: compute_side_effect_profile(x)
            )
            same_dci_candidates = same_dci_candidates[same_dci_candidates["SIDE_EFFECT_PROFILE"].notna()].copy()

            if not same_dci_candidates.empty:
                same_dci_candidates["SIDE_EFFECT_SCORE"] = same_dci_candidates["SIDE_EFFECT_PROFILE"].apply(
                    lambda p: p["score"]
                )

                same_scores = same_dci_candidates["SIDE_EFFECT_SCORE"].dropna().tolist()

                if same_scores and all(score >= base_score for score in same_scores):
                    return {
                        "status": "ok",
                        "reason": "same_or_higher_scores",
                        "base_medicine": medicine_name,
                        "base_row": base_row,
                        "base_profile": base_profile,
                        "alternatives": []
                    }

        return {
            "status": "ok",
            "reason": "no_safer_alternative",
            "base_medicine": medicine_name,
            "base_row": base_row,
            "base_profile": base_profile,
            "alternatives": []
        }

    # Tri :
    # 1) score le plus faible
    # 2) plus grand gain par rapport au médicament de base
    # 3) prix plus bas si dispo
    sort_columns = ["SIDE_EFFECT_SCORE", "SCORE_GAP"]
    ascending_values = [True, False]

    if "PRIX_PUBLIC_NUM" in candidates.columns:
        sort_columns.append("PRIX_PUBLIC_NUM")
        ascending_values.append(True)

    candidates = candidates.sort_values(
        by=sort_columns,
        ascending=ascending_values,
        na_position="last"
    )

        # Déduplication plus intelligente :
    # 1) on évite les doublons de nom commercial
    # 2) on évite d'afficher plusieurs produits avec exactement le même profil d'effets
    cleaned = []
    seen_names = set()
    seen_profiles = set()

    for _, row in candidates.iterrows():
        item = row.to_dict()

        commercial_name = str(item.get("NOM_COMMERCIAL", "")).strip().upper()
        if commercial_name in seen_names:
            continue

        profile = item.get("SIDE_EFFECT_PROFILE", {})
        summary = summarize_profile_hits(profile)

        matched_terms = tuple(sorted([term_name for term_name, _ in profile.get("matched_terms", [])]))
        profile_key = (
            round(float(item.get("SIDE_EFFECT_SCORE", 9999)), 2),
            matched_terms,
            tuple(profile.get("matched_systems", []))
        )

        if profile_key in seen_profiles:
            continue

        seen_names.add(commercial_name)
        seen_profiles.add(profile_key)

        item["SIDE_EFFECT_SUMMARY"] = summary
        cleaned.append(item)

    return {
        "status": "ok",
        "reason": "found",
        "base_medicine": medicine_name,
        "base_row": base_row,
        "base_profile": base_profile,
        "alternatives": cleaned[:top_n]
    }

def build_cheaper_alternative_context(result):
    if result["status"] != "ok" or not result["base_row"]:
        return None

    base = result["base_row"]
    alternatives = result["alternatives"]

    blocks = []
    blocks.append(
        f"""[Médicament de référence]
Nom commercial: {base.get('NOM_COMMERCIAL', '')}
DCI: {base.get('DCI', '')}
Forme: {base.get('FORME', '')}
Dosage: {base.get('DOSAGE_FULL', '')}
Quantité: {base.get('QUANTITE_FULL', '')}
Prix public: {base.get('PRIX_PUBLIC_NUM', '')}"""
    )

    for i, row in enumerate(alternatives, start=1):
        blocks.append(
            f"""[Alternative moins chère {i}]
Nom commercial: {row.get('NOM_COMMERCIAL', '')}
DCI: {row.get('DCI', '')}
Forme: {row.get('FORME', '')}
Dosage: {row.get('DOSAGE_FULL', '')}
Quantité: {row.get('QUANTITE_FULL', '')}
Prix public: {row.get('PRIX_PUBLIC_NUM', '')}"""
        )

    return "\n\n---\n\n".join(blocks)

def fallback_cheaper_alternative_response(result):
    if result["status"] != "ok":
        reason = result.get("reason")

        if reason == "medicine_not_found":
            return "Je n’ai pas pu identifier clairement le médicament demandé dans le dataset."

        if reason == "base_price_missing":
            return "Le médicament demandé a été trouvé, mais son prix public n’est pas exploitable dans le dataset."

        if reason == "base_dci_missing":
            return "Le médicament demandé a été trouvé, mais sa DCI n’est pas disponible dans le dataset."

        if reason == "no_same_dci":
            return "Je n’ai pas trouvé de médicaments avec la même DCI dans le dataset."

        return "Je n’ai pas trouvé d’alternative moins chère dans le dataset."

    base = result["base_row"]
    alternatives = result["alternatives"]

    base_name = base.get("NOM_COMMERCIAL", result.get("base_medicine", "ce médicament"))
    base_price = format_price(base.get("PRIX_PUBLIC_NUM", ""))

    if not alternatives:
        return (
            f"Je n’ai pas trouvé d’alternative moins chère à {base_name} dans le dataset. "
            f"Son prix public est {base_price}."
        )

    lines = [
        f"Voici quelques alternatives moins chères à {base_name} dans le dataset :",
        f"Prix public de {base_name} : {base_price}",
        ""
    ]

    for alt in alternatives:
        lines.append(
            f"- {alt.get('NOM_COMMERCIAL', '')} | "
            f"DCI : {alt.get('DCI', '')} | "
            f"Forme : {alt.get('FORME', '')} | "
            f"Dosage : {alt.get('DOSAGE_FULL', '')} | "
            f"Prix public : {format_price(alt.get('PRIX_PUBLIC_NUM', ''))}"
        )

    return "\n".join(lines)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY manquante ! Crée un fichier .env avec ta clé.")

client = genai.Client(api_key=GEMINI_API_KEY)

def safe_chatbot_response(message, history):
    try:
        response = chatbot_response_hybrid(message, history)
        if response is None:
            return "⚠️ Cet assistant répond uniquement à partir du dataset.\n\nJe n’ai trouvé aucune information correspondante dans le dataset."
        return response
    except Exception as e:
        print("[CHATBOT ERROR]", e)
        return "⚠️ Cet assistant répond uniquement à partir du dataset.\n\nUne erreur technique s’est produite. Veuillez réessayer."

# ── FastAPI Router ────────────────────────────────────────────────
router = APIRouter()

class ChatMessage(BaseModel):
    role: str        # "user" ou "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Envoie un message au chatbot et reçoit une réponse.
    Body JSON :
        {
            "message": "Parle-moi du Doliprane",
            "history": []
        }
    """
    # Convertir l'historique au format attendu par chatbot_response_hybrid
    history = [(m.content, None) if m.role == "user" else (None, m.content)
               for m in (request.history or [])]

    response = safe_chatbot_response(request.message, history)
    return ChatResponse(response=response)

@router.get("/health")
async def health():
    return {"status": "ok", "service": "chatbot"}

