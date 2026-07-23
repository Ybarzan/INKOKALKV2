# Money Leak Calculator — SaaS

Supply Chain Intelligence — La plateforme qui transforme vos donnees logistiques en decisions rentables.

## Lancement rapide

```bash
# 1. Installer les dependances
pip install -r requirements.txt

# 2. Lancer le serveur
python -m uvicorn app.main:app --reload

# 3. Ouvrir dans le navigateur
# API Docs : http://localhost:8000/docs
# Landing  : http://localhost:8000/
```

## Lancer avec Docker

```bash
docker-compose up --build
```

## Tester l'API

```bash
# Lancer le serveur dans un terminal
python -m uvicorn app.main:app --reload

# Dans un autre terminal, lancer les tests
python test_api.py
```

## Structure du projet

```
moneyleak-saas/
├── app/
│   ├── main.py           # Serveur FastAPI
│   ├── auth.py           # Authentification JWT
│   ├── database.py       # Connexion DB (SQLite/PostgreSQL)
│   ├── models.py         # Tables SQL (users, clients, diagnostics)
│   └── routes/
│       ├── diagnostic.py # POST /api/diagnostic → score
│       ├── import_csv.py # POST /api/import → CSV parsing
│       └── auth.py       # POST /api/auth/login, /register
├── landing/
│   └── index.html        # Page marketing
├── requirements.txt      # Dependances Python
├── Dockerfile            # Image Docker
├── docker-compose.yml    # Orchestrateur
├── deploy.sh             # Script de deploiement
└── test_api.py           # Tests de l'API
```

## Endpoints API

| Methode | URL | Description |
|---------|-----|-------------|
| POST | `/api/auth/register` | Creer un compte |
| POST | `/api/auth/login` | Se connecter |
| GET | `/api/auth/me` | Infos utilisateur |
| POST | `/api/diagnostic` | Lancer un diagnostic |
| GET | `/api/diagnostic/secteurs` | Liste des secteurs |
| GET | `/api/diagnostic/indicateurs` | Liste des indicateurs |
| POST | `/api/import/csv` | Importer un CSV |
| GET | `/api/packs` | Packs de services |
| GET | `/api/health` | Health check |

## Technologies

- **FastAPI** — Serveur web rapide (Python)
- **SQLAlchemy** — ORM pour la base de donnees
- **SQLite** — Base de donnees locale (dev) / **PostgreSQL** (prod)
- **JWT** — Authentification par token
- **Docker** — Conteneurisation pour la prod
