"""
Import de factures transporteurs depuis CSV/Excel.
===================================================
Parse les factures et genere automatiquement les indicateurs de diagnostic.

Formats supportes :
  - CSV (separateur ; ou ,)
  - Excel (.xlsx)

Colonnes attendues (flexibles via mapping) :
  - transporteur / carrier
  - poids / weight (kg ou tonnes)
  - distance / km
  - prix / cost / montant (EUR)
  - mode / transport_mode (route/fer/mer/air)
  - date / invoice_date
  - zone / region
"""

from __future__ import annotations
import csv
import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import statistics


@dataclass
class LigneFacture:
    """Ligne de facture transport parsee."""
    transporteur: str = ""
    poids_kg: float = 0.0
    distance_km: float = 0.0
    prix_eur: float = 0.0
    mode: str = "route"
    date: Optional[datetime] = None
    zone: str = ""
    nb_palettes: int = 0
    conteneur_type: str = ""
    
    @property
    def cout_tonne_km(self) -> float:
        """Cout en EUR/tonne.km."""
        if self.poids_kg == 0 or self.distance_km == 0:
            return 0.0
        tonnes = self.poids_kg / 1000
        return self.prix_eur / (tonnes * self.distance_km)
    
    @property
    def cout_palettes_km(self) -> float:
        """Cout EUR/palette/km."""
        if self.nb_palettes == 0 or self.distance_km == 0:
            return 0.0
        return self.prix_eur / (self.nb_palettes * self.distance_km)


# Mapping flexible des colonnes
MAPPING_COLONNES = {
    "transporteur": ["transporteur", "carrier", "carrier_name", "fournisseur"],
    "poids_kg": ["poids", "weight", "poids_kg", "weight_kg", "poids_total"],
    "distance_km": ["distance", "km", "distance_km", "distance_totale"],
    "prix_eur": ["prix", "cost", "montant", "price", "prix_eur", "montant_eur", "total"],
    "mode": ["mode", "transport_mode", "type_transport", "modality"],
    "date": ["date", "invoice_date", "date_facture", "date_livraison"],
    "zone": ["zone", "region", "destination", "area"],
    "nb_palettes": ["palettes", "nb_palettes", "pallets", "nb_pal"],
    "conteneur_type": ["conteneur", "container", "container_type"],
}

SEPARATEURS = [";", ",", "\t"]


class ImporteurFactures:
    """
    Importe et analyse les factures transporteurs.
    
    Utilisation :
        importeur = ImporteurFactures()
        resultats = importeur.importer_csv("factures.csv")
        indicateurs = importeur.calculer_indicateurs()
    """
    
    def __init__(self):
        self.lignes: list[LigneFacture] = []
        self.erreurs: list[str] = []
        self.fichier_source: str = ""
    
    def _detecter_separateur(self, filepath: str) -> str:
        """Detecte automatiquement le separateur du CSV."""
        with open(filepath, "r", encoding="utf-8") as f:
            premiere_ligne = f.readline()
        for sep in SEPARATEURS:
            if sep in premiere_ligne:
                return sep
        return ";"
    
    def _detecter_mapping(self, headers: list[str]) -> dict[str, str]:
        """Detecte automatiquement le mapping des colonnes."""
        mapping = {}
        headers_lower = [h.strip().lower().replace(" ", "_") for h in headers]
        
        for cle, variantes in MAPPING_COLONNES.items():
            for i, header in enumerate(headers_lower):
                if header in variantes:
                    mapping[cle] = headers[i]
                    break
        return mapping
    
    def _parser_valeur(self, valeur: str, type_cible: str) -> float | str | None:
        """Parse une valeur depuis le CSV."""
        if not valeur or valeur.strip() == "":
            return None
        
        valeur = valeur.strip().replace(",", ".").replace("'", "")
        
        if type_cible == "date":
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(valeur, fmt)
                except ValueError:
                    continue
            return None
        
        if type_cible in ("poids_kg", "distance_km", "prix_eur", "nb_palettes"):
            try:
                return float(valeur)
            except ValueError:
                return None
        
        return valeur
    
    def importer_csv(self, filepath: str) -> list[LigneFacture]:
        """
        Importe un fichier CSV de factures.
        
        Returns:
            Liste de LigneFacture parsees
        """
        self.fichier_source = filepath
        self.lignes = []
        self.erreurs = []
        
        if not os.path.exists(filepath):
            self.erreurs.append(f"Fichier non trouve : {filepath}")
            return []
        
        separateur = self._detecter_separateur(filepath)
        
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=separateur)
            headers = next(reader, None)
            
            if not headers:
                self.erreurs.append("Fichier vide ou en-tetes manquants")
                return []
            
            mapping = self._detecter_mapping(headers)
            
            for i, row in enumerate(reader, start=2):
                try:
                    ligne = self._parser_ligne(row, headers, mapping)
                    if ligne:
                        self.lignes.append(ligne)
                except Exception as e:
                    self.erreurs.append(f"Ligne {i} : {str(e)}")
        
        return self.lignes
    
    def _parser_ligne(self, row: list, headers: list, mapping: dict) -> Optional[LigneFacture]:
        """Parse une ligne CSV en LigneFacture."""
        data = {}
        for cle, colonne in mapping.items():
            if colonne in headers:
                idx = headers.index(colonne)
                if idx < len(row):
                    data[cle] = row[idx].strip()
        
        if not data.get("prix_eur"):
            return None
        
        return LigneFacture(
            transporteur=data.get("transporteur", ""),
            poids_kg=self._to_float(data.get("poids_kg", 0)),
            distance_km=self._to_float(data.get("distance_km", 0)),
            prix_eur=self._to_float(data.get("prix_eur", 0)),
            mode=data.get("mode", "route").lower(),
            date=self._parse_date(data.get("date")),
            zone=data.get("zone", ""),
            nb_palettes=int(self._to_float(data.get("nb_palettes", 0))),
            conteneur_type=data.get("conteneur_type", ""),
        )
    
    def _to_float(self, val) -> float:
        try:
            return float(str(val).replace(",", ".").replace("'", "")) if val else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_date(self, val) -> Optional[datetime]:
        if not val:
            return None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                return datetime.strptime(val.strip(), fmt)
            except ValueError:
                continue
        return None
    
    def calculer_indicateurs(self) -> dict[str, float]:
        """
        Calcule les indicateurs de diagnostic depuis les factures.
        
        Returns:
            Dict code_indicateur → valeur calculee
        """
        if not self.lignes:
            return {}
        
        indicateurs = {}
        
        # T06 : Nombre de transporteurs uniques
        transporteurs = set(l.transporteur for l in self.lignes if l.transporteur)
        indicateurs["T06"] = len(transporteurs)
        
        # Cout moyen par mode
        par_mode = {}
        for l in self.lignes:
            if l.mode not in par_mode:
                par_mode[l.mode] = []
            par_mode[l.mode].append(l)
        
        # T02 : Cout EUR/km moyen (route)
        if "route" in par_mode and par_mode["route"]:
            couts_km = [l.prix_eur / l.distance_km for l in par_mode["route"] if l.distance_km > 0]
            if couts_km:
                indicateurs["T02"] = statistics.mean(couts_km)
        
        # T07 : Cout EUR/palette national
        pals_route = [l for l in par_mode.get("route", []) if l.nb_palettes > 0]
        if pals_route:
            couts_pal = [l.prix_eur / l.nb_palettes for l in pals_route]
            indicateurs["T07"] = statistics.mean(couts_pal)
        
        # M04-M07 : Cout EUR/tonne.km par mode
        for mode, code in [("route", "M04"), ("fer", "M05"), ("mer", "M06"), ("air", "M07")]:
            if mode in par_mode and par_mode[mode]:
                couts_tk = [l.cout_tonne_km for l in par_mode[mode] if l.cout_tonne_km > 0]
                if couts_tk:
                    indicateurs[code] = statistics.mean(couts_tk)
        
        # T01 : Cout transport / CA (a fournir avec le CA)
        # Calcule si CA est fourni dans les metadonnees
        
        return indicateurs
    
    def get_statistiques(self) -> dict:
        """Retourne des statistiques descriptives sur les factures."""
        if not self.lignes:
            return {"nb_factures": 0}
        
        couts = [l.prix_eur for l in self.lignes]
        poids = [l.poids_kg for l in self.lignes if l.poids_kg > 0]
        distances = [l.distance_km for l in self.lignes if l.distance_km > 0]
        
        return {
            "nb_factures": len(self.lignes),
            "nb_transporteurs": len(set(l.transporteur for l in self.lignes)),
            "cout_total": sum(couts),
            "cout_moyen": statistics.mean(couts) if couts else 0,
            "cout_median": statistics.median(couts) if couts else 0,
            "poids_total_tonnes": sum(poids) / 1000 if poids else 0,
            "distance_totale_km": sum(distances),
            "modes": dict(
                (mode, len([l for l in self.lignes if l.mode == mode]))
                for mode in set(l.mode for l in self.lignes)
            ),
        }


def generer_csv_template(filepath: str):
    """Genere un fichier CSV template pour l'import."""
    headers = [
        "transporteur", "poids_kg", "distance_km", "prix_eur",
        "mode", "date", "zone", "nb_palettes"
    ]
    exemples = [
        ["Transporteur A", "15000", "350", "4500", "route", "2026-01-15", "Ile-de-France", "12"],
        ["Transporteur B", "25000", "500", "5500", "route", "2026-01-16", "Auvergne-Rhone-Alpes", "20"],
        ["Fret SNCF", "50000", "800", "3200", "fer", "2026-01-17", "Paris-Lyon", "0"],
        ["Maersk", "100000", "12000", "2800", "mer", "2026-01-18", "Asia-Europe", "40"],
    ]
    
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(exemples)
    
    print(f"Template genere : {filepath}")


if __name__ == "__main__":
    # Generer un template pour test
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_factures.csv")
    generer_csv_template(template_path)
    
    # Tester l'import
    importeur = ImporteurFactures()
    resultats = importeur.importer_csv(template_path)
    print(f"\nImport : {len(resultats)} lignes")
    print(f"Statistiques : {importeur.get_statistiques()}")
    indicateurs = importeur.calculer_indicateurs()
    print(f"Indicateurs calcules : {indicateurs}")
