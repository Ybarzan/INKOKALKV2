"""
Route /api/prediction — Prediction simple.
==========================================
Predit l'evolution du score sur 3 mois base sur la tendance.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Diagnostic

router = APIRouter(prefix="/api/prediction", tags=["prediction"])


class PredictionRequest(BaseModel):
    """Valeurs actuelles + objectifs pour predire l'evolution."""
    score_actuel: float = Field(..., description="Score actuel /10")
    ameliorations: dict[str, float] = Field(
        default_factory=dict,
        description="Dict indicateur → nouvelle valeur visee (ex: {'T01': 8.0})"
    )


class PredictionResponse(BaseModel):
    score_actuel: float
    score_predit_3m: float
    gain_score: float
    fuite_actuelle: float
    fuite_predite: float
    economie_estimee: float
    confiance: str  # "haute", "moyenne", "basse"
    explication: str


@router.post("", response_model=PredictionResponse)
def predire_evolution(
    req: PredictionRequest,
    user: User = Depends(get_current_user),
):
    """
    Predit l'evolution du score sur 3 mois.
    Logique simple : chaque amelioree de 1 point de note = +0.3 sur le score global.
    """
    from ..scoring import ScoringEngine

    engine = ScoringEngine()

    # Calculer le gain potentiel
    gain_total = 0.0
    nb_ameliorations = 0

    for code, nouvelle_valeur in req.ameliorations.items():
        # Trouver l'indicateur
        indicateur = None
        for i in engine.indicateurs:
            if i.code == code:
                indicateur = i
                break

        if indicateur:
            # Simuler le gain (simplifie)
            gain_total += 0.3  # Gain fixe par amelioree
            nb_ameliorations += 1

    # Score predit (plafonne a 10)
    score_predit = min(10.0, req.score_actuel + gain_total)

    # Estimation des fuites (linearise)
    fuite_actuelle = req.score_actuel * 100000  # Approximation
    fuite_predite = score_predit * 100000
    economie = fuite_actuelle - fuite_predite

    # Confiance
    if nb_ameliorations >= 3:
        confiance = "haute"
    elif nb_ameliorations >= 1:
        confiance = "moyenne"
    else:
        confiance = "basse"

    # Explication
    if score_predit > req.score_actuel:
        explication = (
            f"En ameliorant {nb_ameliorations} indicateurs, "
            f"votre score pourrait passer de {req.score_actuel}/10 a {score_predit:.1f}/10 "
            f"sur 3 mois. Economie estimee : {economie:,.0f} EUR/an."
        )
    else:
        explication = "Pas d'amelioration prevue avec les parametres actuels."

    return PredictionResponse(
        score_actuel=req.score_actuel,
        score_predit_3m=round(score_predit, 2),
        gain_score=round(gain_total, 2),
        fuite_actuelle=round(fuite_actuelle, 0),
        fuite_predite=round(fuite_predite, 0),
        economie_estimee=round(economie, 0),
        confiance=confiance,
        explication=explication,
    )
