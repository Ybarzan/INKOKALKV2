"""
Route /api/auth — Login / Register / Compte.
=============================================
Le "guichet" d'authentification.
Supporte FR/EN via header Accept-Language.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import (
    hash_password, verify_password, create_access_token, get_current_user
)
from ..models import User
from ..translations import t

router = APIRouter(prefix="/api/auth", tags=["auth"])


# === SCHEMAS ===

class RegisterRequest(BaseModel):
    email: str
    password: str
    nom: str = ""
    prenom: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str


class UserResponse(BaseModel):
    id: int
    email: str
    nom: str
    prenom: str
    role: str


def _get_lang(accept_language: Optional[str] = Header(None)) -> str:
    """Extrait la langue depuis le header Accept-Language."""
    if accept_language and accept_language.startswith("en"):
        return "en"
    return "fr"


# === ROUTES ===

@router.post("/register", response_model=TokenResponse)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    lang: str = Depends(_get_lang),
):
    """Cree un nouveau compte utilisateur."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("email_deja_utilise", lang)
        )

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        nom=req.nom,
        prenom=req.prenom,
        role="consultant",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
    lang: str = Depends(_get_lang),
):
    """Connecte un utilisateur existant."""
    user = db.query(User).filter(User.email == req.email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("email_mdp_incorrect", lang)
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("compte_desactive", lang)
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.get("/me", response_model=UserResponse)
def mon_compte(user: User = Depends(get_current_user)):
    """Recupere les infos de l'utilisateur connecte."""
    return UserResponse(
        id=user.id,
        email=user.email,
        nom=user.nom,
        prenom=user.prenom,
        role=user.role,
    )


@router.get("/languages")
def languages():
    """Liste les langues supportees."""
    return {"languages": ["fr", "en"], "default": "fr"}
