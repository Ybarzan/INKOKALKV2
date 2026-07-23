"""
Route /api/diagnostic — Le coeur du SaaS.
=========================================
Recoit les valeurs d'un client, renvoie le score + recommandations.
Supporte FR/EN via header Accept-Language.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from ..scoring import ScoringEngine, ConfigMission, Domaine, format_eur, format_pct
from ..translations import t

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
    diagnostic_id: Optional[int] = None
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

def _get_lang(accept_language: Optional[str] = Header(None)) -> str:
    """Extrait la langue depuis le header Accept-Language."""
    if accept_language and accept_language.startswith("en"):
        return "en"
    return "fr"


@router.post("", response_model=DiagnosticResponse)
def creer_diagnostic(
    req: ValeursRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: str = Depends(_get_lang),
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
    recommandations = _generer_recommandations(result, lang)

    # Sauvegarder en base (optionnel — ne plante pas si la DB marche pas)
    diagnostic_id = None
    try:
        diagnostic = Diagnostic(
            user_id=user.id,
            titre=req.nom_entreprise or "Diagnostic",
            statut="termine",
            valeurs=req.valeurs,
            score_global=result.score_global,
            fuite_totale_eur=result.fuite_totale_eur,
            fuite_pct_ca=round(result.fuite_pct_ca * 100, 4),
            nb_indicateurs=result.nb_indicateurs,
            nb_critiques=result.nb_critiques,
            resultats_detailles={
                "secteur": req.secteur,
                "domaines": [d.model_dump() for d in domaines],
                "indicateurs": [i.model_dump() for i in indicateurs],
                "recommandations": recommandations,
            },
        )
        db.add(diagnostic)
        db.commit()
        db.refresh(diagnostic)
        diagnostic_id = diagnostic.id
    except Exception as e:
        db.rollback()
        print(f"[WARN] Sauvegarde DB echouee: {e}")

    return DiagnosticResponse(
        diagnostic_id=diagnostic_id,
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


@router.get("/mes-diagnostics")
def mes_diagnostics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste les diagnostics de l'utilisateur connecte."""
    diags = db.query(Diagnostic).filter(
        Diagnostic.user_id == user.id
    ).order_by(Diagnostic.created_at.desc()).limit(50).all()

    return {
        "diagnostics": [
            {
                "id": d.id,
                "titre": d.titre,
                "statut": d.statut,
                "score_global": d.score_global,
                "fuite_totale_eur": d.fuite_totale_eur,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in diags
        ]
    }


@router.get("/{diagnostic_id}")
def get_diagnostic(
    diagnostic_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Recupere un diagnostic par son ID."""
    diag = db.query(Diagnostic).filter(
        Diagnostic.id == diagnostic_id,
        Diagnostic.user_id == user.id,
    ).first()

    if not diag:
        raise HTTPException(404, "Diagnostic non trouve")

    return {
        "id": diag.id,
        "titre": diag.titre,
        "statut": diag.statut,
        "score_global": diag.score_global,
        "fuite_totale_eur": diag.fuite_totale_eur,
        "fuite_pct_ca": diag.fuite_pct_ca,
        "nb_indicateurs": diag.nb_indicateurs,
        "nb_critiques": diag.nb_critiques,
        "valeurs": diag.valeurs,
        "resultats_detailles": diag.resultats_detailles,
        "created_at": diag.created_at.isoformat() if diag.created_at else None,
    }


# === RECOMMANDATIONS ===

def _generer_recommandations(result, lang: str = "fr") -> list[str]:
    """Genere des recommandations basees sur les scores."""
    recos = []

    for domaine, res in result.domaines.items():
        domaine_label = t(domaine.value, lang)
        if res.score < 4:
            recos.append(
                f"🔴 {t('urgent', lang)} — {domaine_label} : score {res.score}/10. "
                f"{res.nb_critiques} {t('indicateurs_critiques', lang).lower()}. "
                f"Audit approfondi recommande."
            )
        elif res.score < 7:
            recos.append(
                f"🟡 {domaine_label} : score {res.score}/10. "
                f"{t('amelioration_possible', lang)} ({res.nb_critiques} points d'attention)."
            )

    # Recommandations specifiques par indicateur
    for domaine, res in result.domaines.items():
        for r in res.indicateurs:
            if r.statut == "critique" and r.indicateur.poids >= 0.03:
                recos.append(
                    f"⚡ {r.indicateur.code} ({r.indicateur.nom}) : "
                    f"{r.valeur_client} vs benchmark {r.benchmark}. "
                    f"{t('potentiel_economie', lang)}."
                )

    if not recos:
        recos.append(f"✅ {t('excellentes_performances', lang)}")

    return recos[:15]
