#!/bin/bash
# === DEPLOY — Money Leak Calculator SaaS ===
# Lance le serveur en mode production (sans Docker)

set -e

echo "========================================="
echo "  Money Leak Calculator — Deploy"
echo "========================================="

# 1. Copier le fichier d'environnement
if [ ! -f .env ]; then
    echo "[1/4] Creation du fichier .env..."
    cp .env.example .env
    echo "  → Fichier .env cree. Editez-le avec vos vrais secrets."
else
    echo "[1/4] Fichier .env deja present."
fi

# 2. Installer les dependances
echo "[2/4] Installation des dependances..."
pip install -r requirements.txt -q

# 3. Initialiser la base de donnees
echo "[3/4] Initialisation de la base de donnees..."
python -c "from app.database import init_db; init_db()"

# 4. Lancer le serveur
echo "[4/4] Demarrage du serveur..."
echo ""
echo "  API Docs : http://localhost:8000/docs"
echo "  Landing  : http://localhost:8000/"
echo "  Health   : http://localhost:8000/api/health"
echo ""
echo "  Ctrl+C pour arreter"
echo "========================================="

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
