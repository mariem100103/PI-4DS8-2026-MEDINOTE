from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ProductItem(BaseModel):
    nom: Optional[str] = None
    commentaire: Optional[str] = None
    opportunites: Optional[str] = None
    benchmarking_concurrents: List[str] = []
    nombre_echantillons: Optional[int] = None


class ReportTemplate(BaseModel):
    nom_prospect: Optional[str] = None
    date_visite: Optional[str] = None
    objectif_visite: Optional[str] = None

    produits_presentes: List[ProductItem] = []

    commentaire: Optional[str] = None
    opportunites: Optional[str] = None
    benchmarking_concurrents: List[str] = []

    nombre_echantillons: Optional[int] = None
    nom_superviseur: Optional[str] = None
    nombre_patients_presents: Optional[int] = None
    gadget: Optional[str] = None

    remarque_generale: Optional[str] = None
    date_relance: Optional[str] = None
    prochaine_etape: Optional[str] = None


class ReportResponse(BaseModel):
    success: bool
    report_id: int
    data: Dict[str, Any]