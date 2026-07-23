"""
Systeme d'API Keys.
===================
Permet de gerer les acces par cle API (rate limiting, tracking).
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets
import hashlib

from .models import Base


class APIKey(Base):
    """Cle API pour un utilisateur."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)  # Les 8 premiers chars
    nom = Column(String(255), default="API Key")
    is_active = Column(Boolean, default=True)
    
    # Rate limiting
    requests_today = Column(Integer, default=0)
    requests_limit = Column(Integer, default=1000)  # Par jour
    last_reset = Column(DateTime, default=datetime.utcnow)
    
    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

    # Relation
    user = relationship("User")


def generer_api_key() -> tuple[str, str, str]:
    """
    Genere une nouvelle API key.
    Retourne (key_complete, key_hash, key_prefix)
    """
    key = f"mlk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12]
    return key, key_hash, key_prefix


def hasher_api_key(key: str) -> str:
    """Hash une API key pour la stocker en base."""
    return hashlib.sha256(key.encode()).hexdigest()
