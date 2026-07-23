"""
Route /api/rapport — Generation de rapports PDF.
=================================================
Genere un rapport de diagnostic complet au format PDF.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
import io

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Diagnostic
from ..pdf_generator import generer_rapport_pdf

router = APIRouter(prefix="/api/rapport", tags=["rapport"])


class RapportRequest(BaseModel):
    """Parametres pour generer le rapport PDF."""
    secteur: str = Field(default="Industrie")
    ca_annuel_ht: float = Field(default=10_000_000)
    nom_entreprise: str = Field(default="")
    score_global: float = Field(default=0)
    fuite_totale_eur: float = Field(default=0)
    fuite_pct_ca: float = Field(default=0)
    nb_indicateurs: int = Field(default=0)
    nb_critiques: int = Field(default=0)
    nb_quick_wins: int = Field(default=0)
    domaines: list[dict] = Field(default_factory=list)
    indicateurs: list[dict] = Field(default_factory=list)
    recommandations: list[str] = Field(default_factory=list)


@router.post("/pdf")
def generer_pdf(
    req: RapportRequest,
    user: User = Depends(get_current_user),
):
    """
    Genere un rapport PDF du diagnostic.
    Retourne le fichier PDF en telechargement.
    """
    pdf_bytes = generer_rapport_pdf(
        score_global=req.score_global,
        fuite_totale_eur=req.fuite_totale_eur,
        fuite_pct_ca=req.fuite_pct_ca,
        nb_indicateurs=req.nb_indicateurs,
        nb_critiques=req.nb_critiques,
        nb_quick_wins=req.nb_quick_wins,
        domaines=req.domaines,
        indicateurs=req.indicateurs,
        recommandations=req.recommandations,
        secteur=req.secteur,
        nom_entreprise=req.nom_entreprise,
        ca_annuel_ht=req.ca_annuel_ht,
    )

    filename = f"MoneyLeak_Diagnostic_{req.nom_entreprise or 'Client'}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )


@router.get("/diagnostic/{diagnostic_id}/pdf")
def telecharger_pdf_diagnostic(
    diagnostic_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Telecharge le PDF d'un diagnostic sauvegarde en base.
    """
    diag = db.query(Diagnostic).filter(
        Diagnostic.id == diagnostic_id,
        Diagnostic.user_id == user.id,
    ).first()

    if not diag:
        raise HTTPException(404, "Diagnostic non trouve")

    pdf_bytes = generer_rapport_pdf(
        score_global=diag.score_global or 0,
        fuite_totale_eur=diag.fuite_totale_eur or 0,
        fuite_pct_ca=diag.fuite_pct_ca or 0,
        nb_indicateurs=diag.nb_indicateurs,
        nb_critiques=diag.nb_critiques,
        nb_quick_wins=0,
        domaines=diag.resultats_detailles.get("domaines", []) if diag.resultats_detailles else [],
        indicateurs=diag.resultats_detailles.get("indicateurs", []) if diag.resultats_detailles else [],
        recommandations=diag.resultats_detailles.get("recommandations", []) if diag.resultats_detailles else [],
        secteur=diag.resultats_detailles.get("secteur", "") if diag.resultats_detailles else "",
        nom_entreprise=diag.titre or "",
        ca_annuel_ht=0,
    )

    filename = f"MoneyLeak_Diagnostic_{diag.id}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )
