"""
Route /api/keys — Gestion des API Keys.
========================================
Cree, liste et gere les API keys pour le rate limiting.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..models_apikey import APIKey, generer_api_key, hasher_api_key

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class CreateKeyRequest(BaseModel):
    nom: str = Field(default="API Key", description="Nom de la cle")
    requests_limit: int = Field(default=1000, description="Requetes/jour max")


class KeyResponse(BaseModel):
    id: int
    nom: str
    key_prefix: str
    is_active: bool
    requests_today: int
    requests_limit: int
    created_at: str
    last_used: Optional[str] = None


@router.post("", response_model=dict)
def creer_api_key(
    req: CreateKeyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cree une nouvelle API key."""
    key_complete, key_hash, key_prefix = generer_api_key()

    api_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        nom=req.nom,
        requests_limit=req.requests_limit,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {
        "id": api_key.id,
        "nom": api_key.nom,
        "key": key_complete,  # Affichee une seule fois !
        "key_prefix": key_prefix,
        "requests_limit": api_key.requests_limit,
        "message": "Copiez cette cle — elle ne sera plus affichee.",
    }


@router.get("", response_model=list[KeyResponse])
def lister_api_keys(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste les API keys de l'utilisateur."""
    keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return [
        KeyResponse(
            id=k.id,
            nom=k.nom,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            requests_today=k.requests_today,
            requests_limit=k.requests_limit,
            created_at=k.created_at.isoformat() if k.created_at else "",
            last_used=k.last_used.isoformat() if k.last_used else None,
        )
        for k in keys
    ]


@router.delete("/{key_id}")
def supprimer_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Supprime une API key."""
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user.id,
    ).first()

    if not key:
        raise HTTPException(404, "API key non trouvee")

    db.delete(key)
    db.commit()
    return {"success": True, "message": "API key supprimee"}


@router.post("/{key_id}/toggle")
def toggle_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Active/desactive une API key."""
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user.id,
    ).first()

    if not key:
        raise HTTPException(404, "API key non trouvee")

    key.is_active = not key.is_active
    db.commit()
    return {"success": True, "is_active": key.is_active}


def verifier_api_key(
    api_key: str,
    db: Session,
) -> Optional[User]:
    """
    Verifie une API key et retourne l'utilisateur.
    Utilise comme dependency dans les routes protegees.
    """
    key_hash = hasher_api_key(api_key)
    key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True,
    ).first()

    if not key:
        return None

    # Verifier le rate limit
    now = datetime.utcnow()
    if key.last_reset and (now - key.last_reset).days >= 1:
        key.requests_today = 0
        key.last_reset = now

    if key.requests_today >= key.requests_limit:
        return None  # Rate limit depasse

    # Incrementer le compteur
    key.requests_today += 1
    key.last_used = now
    db.commit()

    # Retourner l'utilisateur
    return db.query(User).filter(User.id == key.user_id).first()
