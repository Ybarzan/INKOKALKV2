"""
Connexion a la base de donnees.
===============================
Supporte PostgreSQL (prod) et SQLite (dev local).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from .models import Base

# URL de connexion
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Render fournit parfois postgres:// au lieu de postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Si pas de DATABASE_URL, fallback SQLite local
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./moneyleak.db"
    print("[INFO] Pas de DATABASE_URL, fallback SQLite local")

_is_sqlite = "sqlite" in DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)

# Activer les FK en SQLite
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI : fournit une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cree toutes les tables (a lancer au demarrage)."""
    Base.metadata.create_all(bind=engine)
    if _is_sqlite:
        print("[OK] SQLite : moneyleak.db")
    else:
        print("[OK] PostgreSQL connecte")
