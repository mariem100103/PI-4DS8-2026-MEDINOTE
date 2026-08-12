# ================================================================
# routers/data.py — CRM Médical · FastAPI
# ================================================================

from fastapi import APIRouter, Query
from services.extraction_service import load_data

router = APIRouter(prefix="/data", tags=["Données"])


@router.get("/stats")
async def dataset_stats():
    """Statistiques générales sur le dataset chargé."""
    df, df_meds = load_data()
    return {
        "notes_count":       len(df) if df is not None else 0,
        "medicaments_count": len(df_meds) if df_meds is not None else 0,
        "columns_notes":     list(df.columns) if df is not None else [],
        "columns_meds":      list(df_meds.columns) if df_meds is not None else [],
    }


@router.get("/medicaments")
async def search_medicaments(q: str = Query(default="", min_length=0)):
    """Recherche un médicament dans la base medicaments_final."""
    _, df_meds = load_data()
    if df_meds is None or df_meds.empty:
        return {"results": []}
    mask = (
        df_meds["NOM_COMMERCIAL"].str.contains(q, case=False, na=False)
        | df_meds["DCI"].str.contains(q, case=False, na=False)
    ) if q else df_meds.index == df_meds.index  # all rows if empty query
    results = df_meds[mask].head(20).to_dict(orient="records")
    return {"results": results, "total": int(df_meds[mask].shape[0])}
