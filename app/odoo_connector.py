"""
Connecteur Odoo — Import/Export de donnees.
============================================
Connecte Money Leak Calculator a Odoo via l'API XML-RPC.
"""

import xmlrpc.client
import json
from typing import Optional


class OdooConnector:
    """
    Connecteur pour Odoo ERP.
    
    Utilisation :
        odoo = OdooConnector("https://mon-odoo.com", "admin", "mot_de_passe")
        odoo.connecter()
        factures = odoo.importer_factures_transport()
    """

    def __init__(
        self,
        url: str,
        login: str,
        password: str,
        db: str = "",
    ):
        self.url = url.rstrip("/")
        self.login = login
        self.password = password
        self.db = db
        self.uid = None
        self.models = None

    def connecter(self) -> bool:
        """Connecte a Odoo et authentifie."""
        try:
            # 1. Detecter la DB si pas fournie
            if not self.db:
                common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
                dbs = common.list()
                if dbs:
                    self.db = dbs[0]
                else:
                    return False

            # 2. Authentifier
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.uid = common.authenticate(self.db, self.login, self.password, {})
            if not self.uid:
                return False

            # 3. Preparer les modeles
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
            return True

        except Exception as e:
            print(f"[ERREUR] Connexion Odoo: {e}")
            return False

    def _search_read(self, model: str, domain: list, fields: list, limit: int = 1000) -> list:
        """Recherche et lit des enregistrements."""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, "search_read",
            [domain],
            {"fields": fields, "limit": limit},
        )

    def importer_factures_transport(self) -> list[dict]:
        """
        Importe les factures de transport depuis Odoo.
        Modele : account.move (factures fournisseurs) avec picking_ids.
        """
        factures = self._search_read(
            "account.move",
            [("move_type", "=", "in_invoice")],  # Factures fournisseurs
            [
                "invoice_date", "partner_id", "invoice_origin",
                "invoice_line_ids", "amount_total",
            ],
            limit=500,
        )

        resultats = []
        for f in factures:
            resultats.append({
                "date": str(f.get("invoice_date", "")),
                "fournisseur": f.get("partner_id", [1, ""])[1] if isinstance(f.get("partner_id"), list) else "",
                "reference": f.get("invoice_origin", ""),
                "montant": f.get("amount_total", 0),
            })

        return resultats

    def importer_stock_moves(self) -> list[dict]:
        """
        Importe les mouvements de stock depuis Odoo.
        Modele : stock.move
        """
        moves = self._search_read(
            "stock.move",
            [("state", "=", "done")],
            [
                "date", "product_id", "location_id",
                "location_dest_id", "product_uom_qty",
                "product_uom",
            ],
            limit=1000,
        )

        resultats = []
        for m in moves:
            resultats.append({
                "date": str(m.get("date", "")),
                "produit": m.get("product_id", [1, ""])[1] if isinstance(m.get("product_id"), list) else "",
                "quantite": m.get("product_uom_qty", 0),
                "unite": m.get("product_uom", [1, ""])[1] if isinstance(m.get("product_uom"), list) else "",
            })

        return resultats

    def exporter_diagnostic(self, diagnostic: dict) -> Optional[int]:
        """
        Exporte un diagnostic vers Odoo comme note/activite.
        Modele : account.analytic.line ou mail.message
        """
        try:
            note_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                "mail.message", "create",
                [{
                    "model": "res.partner",
                    "res_id": 1,
                    "message_type": "notification",
                    "subject": f"Diagnostic Supply Chain - Score {diagnostic.get('score_global', 0)}/10",
                    "body": json.dumps(diagnostic, ensure_ascii=False, indent=2),
                }],
            )
            return note_id
        except Exception as e:
            print(f"[ERREUR] Export Odoo: {e}")
            return None

    def get_info(self) -> dict:
        """Retourne les infos de connexion."""
        return {
            "url": self.url,
            "db": self.db,
            "uid": self.uid,
            "connecte": self.uid is not None,
        }


# === ROUTE API ===

def creer_route_odoo():
    """Cree le router FastAPI pour les routes Odoo."""
    from fastapi import APIRouter, Depends, HTTPException
    from pydantic import BaseModel, Field
    from ..auth import get_current_user
    from ..models import User

    router = APIRouter(prefix="/api/odoo", tags=["odoo"])

    class OdooConnectRequest(BaseModel):
        url: str = Field(..., description="URL de l'instance Odoo")
        login: str = Field(..., description="Login Odoo")
        password: str = Field(..., description="Mot de passe Odoo")
        db: str = Field(default="", description="Nom de la base Odoo (optionnel)")

    @router.post("/connect")
    def connecter_odoo(
        req: OdooConnectRequest,
        user: User = Depends(get_current_user),
    ):
        """Connecte a une instance Odoo."""
        odoo = OdooConnector(req.url, req.login, req.password, req.db)
        success = odoo.connecter()

        if not success:
            raise HTTPException(400, "Connexion Odoo echouee — verifiez les identifiants")

        return {
            "success": True,
            "info": odoo.get_info(),
        }

    @router.post("/import/factures")
    def import_factures_odoo(
        req: OdooConnectRequest,
        user: User = Depends(get_current_user),
    ):
        """Importe les factures de transport depuis Odoo."""
        odoo = OdooConnector(req.url, req.login, req.password, req.db)
        if not odoo.connecter():
            raise HTTPException(400, "Connexion Odoo echouee")

        factures = odoo.importer_factures_transport()
        return {
            "success": True,
            "nb_factures": len(factures),
            "factures": factures[:100],  # Limiter a 100 pour la reponse
        }

    @router.post("/import/stock")
    def import_stock_odoo(
        req: OdooConnectRequest,
        user: User = Depends(get_current_user),
    ):
        """Importe les mouvements de stock depuis Odoo."""
        odoo = OdooConnector(req.url, req.login, req.password, req.db)
        if not odoo.connecter():
            raise HTTPException(400, "Connexion Odoo echouee")

        moves = odoo.importer_stock_moves()
        return {
            "success": True,
            "nb_moves": len(moves),
            "moves": moves[:100],
        }

    return router
