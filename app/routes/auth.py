"""
Route /api/auth — Login / Register / Compte.
=============================================
Le "guichet" d'authentification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import (
    hash_password, verify_password, create_access_token, get_current_user
)
from ..models import User

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


# === ROUTES ===

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Cree un nouveau compte utilisateur."""
    # Verifier si l'email existe deja
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est deja utilise"
        )

    # Creer l'utilisateur
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

    # Generer le token
    token = create_access_token({"sub": str(user.id), "email": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Connecte un utilisateur existant."""
    user = db.query(User).filter(User.email == req.email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte desactive"
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
