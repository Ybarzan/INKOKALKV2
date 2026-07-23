"""
Route /api/import — Import de factures CSV.
===========================================
Parse un fichier CSV de factures transporteurs et renvoie les indicateurs calcules.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import sys
import os
import tempfile

from ..import_factures import ImporteurFactures

from ..database import get_db
from ..auth import get_current_user
from ..models import User

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/csv")
async def importer_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Importe un fichier CSV de factures transporteurs.
    Parse les donnees et renvoie les indicateurs calcules automatiquement.
    """
    # Verifier le type de fichier
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(400, "Seuls les fichiers CSV sont supportes")

    # Sauvegarder temporairement le fichier
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", mode="wb"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Parser le CSV
        importeur = ImporteurFactures()
        lignes = importeur.importer_csv(tmp_path)

        if not lignes:
            return JSONResponse(
                status_code=400,
                content={
                    "erreur": "Aucune donnee exploitable",
                    "details": importeur.erreurs,
                },
            )

        # Calculer les indicateurs
        indicateurs = importeur.calculer_indicateurs()
        stats = importeur.get_statistiques()

        return {
            "success": True,
            "nb_lignes": len(lignes),
            "stats": stats,
            "indicateurs_calcules": indicateurs,
            "erreurs": importeur.erreurs,
        }

    except Exception as e:
        raise HTTPException(500, f"Erreur lors de l'import : {str(e)}")

    finally:
        # Nettoyer le fichier temporaire
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/template")
def telecharger_template():
    """
    Genere et telecharge un fichier CSV template.
    Utilise pour guider l'utilisateur dans le format d'import.
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "transporteur", "poids_kg", "distance_km", "prix_eur",
        "mode", "date", "zone", "nb_palettes"
    ])
    writer.writerow([
        "Transporteur A", "15000", "350", "4500",
        "route", "2026-01-15", "Ile-de-France", "12"
    ])
    writer.writerow([
        "Transporteur B", "25000", "500", "5500",
        "route", "2026-01-16", "Auvergne-Rhone-Alpes", "20"
    ])
    writer.writerow([
        "Fret SNCF", "50000", "800", "3200",
        "fer", "2026-01-17", "Paris-Lyon", "0"
    ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=template_factures.csv"
        },
    )
