"""
Money Leak Calculator — API SaaS
=================================
Le serveur principal FastAPI.
Lance avec : uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import init_db
from .routes.diagnostic import router as diagnostic_router
from .routes.import_csv import router as import_router
from .routes.auth import router as auth_router
from .routes.rapport import router as rapport_router
from .routes.prediction import router as prediction_router

# === CREER L'APP ===
app = FastAPI(
    title="Money Leak Calculator API",
    description="Supply Chain Intelligence — Detectez et quantifiez les fuites de rentabilite",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# === CORS (pour le widget Excel + dashboard) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, limiter aux domaines autorises
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTES ===
app.include_router(auth_router)
app.include_router(diagnostic_router)
app.include_router(import_router)
app.include_router(rapport_router)
app.include_router(prediction_router)


# === ROUTES PUBLIQUES ===

@app.get("/")
def accueil():
    """Page d'accueil — redirige vers la landing page."""
    landing_path = os.path.join(os.path.dirname(__file__), "..", "landing", "index.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    return {
        "name": "Money Leak Calculator API",
        "version": "4.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/api/health")
def health():
    """Health check pour le monitoring."""
    return {"status": "ok", "version": "4.0.0"}


@app.get("/api/packs")
def lister_packs():
    """Liste les packs de services disponibles."""
    return {
        "packs": [
            {
                "nom": "Fuite Scan",
                "tarif": "18 000 - 25 000 EUR",
                "duree": "3-4 semaines",
                "description": "Diagnostic flash des fuites de rentabilite",
            },
            {
                "nom": "Redesign Express",
                "tarif": "45 000 - 65 000 EUR",
                "duree": "3 mois",
                "description": "Quick wins + projets structurants",
            },
            {
                "nom": "Redesign Total",
                "tarif": "90 000 - 180 000 EUR",
                "duree": "6-12 mois",
                "description": "Transformation complete de la Supply Chain",
            },
            {
                "nom": "Transfert",
                "tarif": "8 000 - 15 000 EUR/mois",
                "duree": "Mensuel",
                "description": "Formation + coaching des equipes",
            },
        ]
    }


# === DEMARRAGE ===

@app.on_event("startup")
def startup():
    """Initialise la base de donnees au demarrage."""
    init_db()
    print("=" * 50)
    print("  Money Leak Calculator API — Running")
    print("  Docs : http://localhost:8000/docs")
    print("  Landing : http://localhost:8000/")
    print("=" * 50)


# === SERVEUR LOCAL ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
