"""
Route /api/diagnostic — Le coeur du SaaS.
==========================================
Recoit les valeurs d'un client, renvoie le score + recommandations.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from ..scoring import ScoringEngine, ConfigMission, Domaine, format_eur, format_pct

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Client, Diagnostic

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])

# Moteur de scoring (singleton — charge une seule fois)
_engine = None

def get_engine() -> ScoringEngine:
    global _engine
    if _engine is None:
        _engine = ScoringEngine()
    return _engine


# === SCHEMAS PYDANTIC ===

class ValeursRequest(BaseModel):
    """Les valeurs des indicateurs saisies par le client."""
    secteur: str = Field(..., description="Secteur d'activite")
    ca_annuel_ht: float = Field(..., gt=0, description="Chiffre d'affaires annuel HT")
    nom_entreprise: str = Field(default="Client")
    valeurs: dict[str, float] = Field(
        ...,
        description="Dict code_indicateur → valeur (ex: {'T01': 14.0, 'S01': 50})"
    )


class IndicateurResult(BaseModel):
    code: str
    nom: str
    domaine: str
    valeur: float
    benchmark: float
    ecart_pct: float
    note: int
    statut: str


class DomaineResult(BaseModel):
    domaine: str
    score: float
    nb_indicateurs: int
    nb_critiques: int


class DiagnosticResponse(BaseModel):
    score_global: float
    fuite_totale_eur: float
    fuite_pct_ca: float
    nb_indicateurs: int
    nb_critiques: int
    nb_quick_wins: int
    domaines: list[DomaineResult]
    indicateurs_detailles: list[IndicateurResult]
    recommandations: list[str]


# === ROUTES ===

@router.post("", response_model=DiagnosticResponse)
def creer_diagnostic(
    req: ValeursRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Lance un diagnostic complet.
    Recoit les valeurs, renvoie le score + recommandations.
    """
    engine = get_engine()

    # Config de mission
    config = ConfigMission(
        nom_entreprise=req.nom_entreprise,
        secteur=req.secteur,
        ca_annuel_ht=req.ca_annuel_ht,
    )

    # Lancer le scoring
    result = engine.diagnoser(config, req.valeurs)

    # Construire les domaines
    domaines = []
    for domaine, res in result.domaines.items():
        domaines.append(DomaineResult(
            domaine=domaine.value,
            score=res.score,
            nb_indicateurs=res.nb_indicateurs,
            nb_critiques=res.nb_critiques,
        ))

    # Construire les indicateurs detailles
    indicateurs = []
    for domaine, res in result.domaines.items():
        for r in res.indicateurs:
            indicateurs.append(IndicateurResult(
                code=r.indicateur.code,
                nom=r.indicateur.nom,
                domaine=r.indicateur.domaine.value,
                valeur=r.valeur_client,
                benchmark=r.benchmark,
                ecart_pct=round(r.ecart_pct * 100, 1),
                note=r.note,
                statut=r.statut,
            ))

    # Generer les recommandations
    recommandations = _generer_recommandations(result)

    return DiagnosticResponse(
        score_global=result.score_global,
        fuite_totale_eur=result.fuite_totale_eur,
        fuite_pct_ca=round(result.fuite_pct_ca * 100, 2),
        nb_indicateurs=result.nb_indicateurs,
        nb_critiques=result.nb_critiques,
        nb_quick_wins=result.nb_quick_wins,
        domaines=domaines,
        indicateurs_detailles=indicateurs,
        recommandations=recommandations,
    )


@router.get("/secteurs")
def lister_secteurs():
    """Liste les secteurs disponibles."""
    engine = get_engine()
    return {"secteurs": engine.get_liste_secteurs()}


@router.get("/indicateurs")
def lister_indicateurs():
    """Liste tous les indicateurs de diagnostic."""
    engine = get_engine()
    return {
        "indicateurs": [
            {
                "code": i.code,
                "nom": i.nom,
                "domaine": i.domaine.value,
                "unite": i.unite,
                "critere": i.critere.value,
            }
            for i in engine.indicateurs
        ]
    }


# === RECOMMANDATIONS ===

def _generer_recommandations(result) -> list[str]:
    """Genere des recommandations basees sur les scores."""
    recos = []

    for domaine, res in result.domaines.items():
        if res.score < 4:
            recos.append(
                f"🔴 URGENT — {domaine.value} : score {res.score}/10. "
                f"{res.nb_critiques} indicateurs critiques. Audit approfondi recommande."
            )
        elif res.score < 7:
            recos.append(
                f"🟡 {domaine.value} : score {res.score}/10. "
                f"Des quick wins sont possibles ({res.nb_critiques} points d'attention)."
            )

    # Recommandations specifiques par indicateur
    for domaine, res in result.domaines.items():
        for r in res.indicateurs:
            if r.statut == "critique" and r.indicateur.poids >= 0.03:
                recos.append(
                    f"⚡ {r.indicateur.code} ({r.indicateur.nom}) : "
                    f"{r.valeur_client} vs benchmark {r.benchmark}. "
                    f"Potentiel d'economie estime."
                )

    if not recos:
        recos.append("✅ Excellentes performances ! Pas de fuite majeure detectee.")

    return recos[:15]  # Limiter a 15 recommandations
