"""
Authentification JWT (login/register).
======================================
Le "passeport" de la plateforme.
Chaque utilisateur a un email + mot de passe.
Le serveur donne un "jeton" (token) qui prouve qui il est.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from .database import get_db
from .models import User

# === CONFIG ===
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# === BEARER TOKEN ===
security = HTTPBearer()


# --- FONCTIONS UTILITAIRES ---

def hash_password(password: str) -> str:
    """Hash un mot de passe (pour le stocker en base)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifie si un mot de passe correspond au hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cree un token JWT.
    C'est comme un "passeport" temporaire qui expire au bout de X heures.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode un token JWT.
    Si le token est invalide ou expire, leve une erreur.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expire",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- DEPENDENCY FASTAPI ---

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extrait l'utilisateur courant depuis le token.
    Utilise comme dependency dans les routes protegees :
        @app.get("/me")
        def mon_compte(user: User = Depends(get_current_user)):
            return user
    """
    payload = decode_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=401, detail="Token invalide")
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur non trouve")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte desactive")
    return user
