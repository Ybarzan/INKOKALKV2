"""
Tables de la base de donnees (SQLAlchemy).
==========================================
Chaque client a ses propres donnees (multi-tenant).
"""

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey, JSON, Boolean, Text
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Un utilisateur de la plateforme (consultant ou admin)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nom = Column(String(255), default="")
    prenom = Column(String(255), default="")
    role = Column(String(50), default="consultant")  # admin, consultant, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    diagnostics = relationship("Diagnostic", back_populates="owner")


class Client(Base):
    """Un client du consultant (entreprise diagnostiquee)."""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nom = Column(String(255), nullable=False)
    secteur = Column(String(100), default="Industrie")
    pays = Column(String(100), default="France")
    ca_annuel_ht = Column(Float, default=10_000_000.0)
    effectif_total = Column(Integer, default=50)
    effectif_sc = Column(Integer, default=8)
    devise = Column(String(10), default="EUR")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    diagnostics = relationship("Diagnostic", back_populates="client")


class Diagnostic(Base):
    """Un diagnostic effectue sur un client."""
    __tablename__ = "diagnostics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    titre = Column(String(255), default="Diagnostic")
    statut = Column(String(50), default="brouillon")  # brouillon, termine, archive

    # Parametres
    ponderations = Column(JSON, default=dict)
    seuils = Column(JSON, default=dict)

    # Valeurs saisies (code_indicateur → valeur)
    valeurs = Column(JSON, default=dict)

    # Resultats (mis a jour apres calcul)
    score_global = Column(Float, nullable=True)
    fuite_totale_eur = Column(Float, nullable=True)
    fuite_pct_ca = Column(Float, nullable=True)
    nb_indicateurs = Column(Integer, default=0)
    nb_critiques = Column(Integer, default=0)
    resultats_detailles = Column(JSON, default=dict)

    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    owner = relationship("User", back_populates="diagnostics")
    client = relationship("Client", back_populates="diagnostics")
