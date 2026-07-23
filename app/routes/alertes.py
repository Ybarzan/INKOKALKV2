"""
Route /api/alertes — Alertes email.
====================================
Envoie des alertes email quand des KPI sont critiques.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..email_alerts import AlertEmail

router = APIRouter(prefix="/api/alertes", tags=["alertes"])


class AlerteRequest(BaseModel):
    destinataire: str = Field(..., description="Email du destinataire")
    score: float = Field(..., description="Score actuel /10")
    critiques: list[str] = Field(default_factory=list, description="Liste des KPI critiques")
    fuite_eur: float = Field(default=0, description="Fuite totale en EUR")
    secteur: str = Field(default="", description="Secteur d'activite")
    nom_entreprise: str = Field(default="", description="Nom de l'entreprise")


class RapportEmailRequest(BaseModel):
    destinataire: str = Field(..., description="Email du destinataire")
    score: float = Field(...)
    fuite_eur: float = Field(...)
    fuite_pct: float = Field(...)
    nb_critiques: int = Field(...)
    recommandations: list[str] = Field(default_factory=list)
    secteur: str = Field(default="")
    nom_entreprise: str = Field(default="")


@router.post("/send")
def envoyer_alerte(
    req: AlerteRequest,
    user: User = Depends(get_current_user),
):
    """Envoie une alerte email pour des KPI critiques."""
    alerter = AlertEmail()
    success = alerter.envoyer_alerte(
        destinataire=req.destinataire,
        score=req.score,
        critiques=req.critiques,
        fuite_eur=req.fuite_eur,
        secteur=req.secteur,
    )
    if success:
        return {"success": True, "message": f"Alerte envoyee a {req.destinataire}"}
    else:
        raise HTTPException(500, "Echec envoi email — SMTP non configure")


@router.post("/rapport")
def envoyer_rapport(
    req: RapportEmailRequest,
    user: User = Depends(get_current_user),
):
    """Envoie le rapport complet par email."""
    alerter = AlertEmail()
    success = alerter.envoyer_rapport(
        destinataire=req.destinataire,
        score=req.score,
        fuite_eur=req.fuite_eur,
        fuite_pct=req.fuite_pct,
        nb_critiques=req.nb_critiques,
        recommandations=req.recommandations,
        secteur=req.secteur,
        nom_entreprise=req.nom_entreprise,
    )
    if success:
        return {"success": True, "message": f"Rapport envoye a {req.destinataire}"}
    else:
        raise HTTPException(500, "Echec envoi email — SMTP non configure")


@router.get("/config")
def config_smtp():
    """Verifie la configuration SMTP."""
    import os
    return {
        "smtp_configured": bool(os.getenv("SMTP_USER")),
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    }
