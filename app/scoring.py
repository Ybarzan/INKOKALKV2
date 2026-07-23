"""
Moteur de scoring Supply Chain — Six Sigma Quality
===================================================
Module independant de toute dependance Excel/API/DB.
Logique pure : entrees → scores → recommandations.

Architecture :
  - Pas de dependance openpyxl (rendu separe)
  - Toutes les constantes dans benchmarks.json
  - Fonctions pures, testables, documentees
  - Versioning interne (MAJOR.MINOR.PATCH)

Auteur : SC&T Consulting
Version : 4.0.0
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import os


# ============================================================================
# CONSTANTS
# ============================================================================

ENGINE_VERSION = "4.0.0"

class Domaine(Enum):
    TRANSPORT = "TRANSPORT"
    STOCKS = "STOCKS"
    ENTREPOT = "ENTREPOT"
    PROCESSUS = "PROCESSUS"
    ACHATS = "ACHATS"


class CritereScoring(Enum):
    """Criteres de notation : min = valeur <= benchmark est optimal."""
    MIN = "min"  # Plus c'est bas, mieux c'est (ex: cout transport)
    MAX = "max"  # Plus c'est haut, mieux c'est (ex: taux chargement)


# Ponderations par defaut (somme = 1.0)
PONDERATIONS_DEFAUT = {
    Domaine.TRANSPORT: 0.30,
    Domaine.STOCKS: 0.25,
    Domaine.ENTREPOT: 0.20,
    Domaine.PROCESSUS: 0.15,
    Domaine.ACHATS: 0.10,
}

# Seuils de notation par defaut
SEUILS_DEFAUT = {
    "note_max": 10,
    "vert_tolerance": 1.0,    # valeur <= benchmark * 1.0 → note 10
    "seuil_jaune": 1.2,       # valeur <= benchmark * 1.2 → note 7
    "seuil_orange": 1.5,      # valeur <= benchmark * 1.5 → note 4
    # Au-dela → note 1
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Indicateur:
    """Definition d'un indicateur de diagnostic."""
    code: str
    nom: str
    domaine: Domaine
    unite: str
    benchmark_defaut: float
    poids: float
    critere: CritereScoring
    row_excel: int = 0  # Position dans le fichier Excel (optionnel)


@dataclass
class ResultatIndicateur:
    """Resultat du scoring pour un indicateur."""
    indicateur: Indicateur
    valeur_client: float
    benchmark: float
    ecart_pct: float
    note: int
    score_pondere: float
    statut: str  # "optimal", "correct", "attention", "critique"


@dataclass
class ResultatDomaine:
    """Score agrege d'un domaine."""
    domaine: Domaine
    score: float
    nb_indicateurs: int
    nb_critiques: int
    indicateurs: list[ResultatIndicateur] = field(default_factory=list)


@dataclass
class DiagnosticComplet:
    """Resultat complet d'un diagnostic."""
    score_global: float
    domaines: dict[Domaine, ResultatDomaine]
    fuite_totale_eur: float
    fuite_pct_ca: float
    nb_indicateurs: int
    nb_critiques: int
    nb_quick_wins: int


@dataclass
class ConfigMission:
    """Parametres d'une mission de diagnostic."""
    nom_entreprise: str = "Client X"
    secteur: str = "Industrie"
    pays: str = "France"
    ca_annuel_ht: float = 10_000_000.0
    effectif_total: int = 50
    effectif_sc: int = 8
    devise: str = "EUR"
    consultant: str = ""
    ponderations: dict[Domaine, float] = field(
        default_factory=lambda: dict(PONDERATIONS_DEFAUT)
    )
    seuils: dict[str, float] = field(
        default_factory=lambda: dict(SEUILS_DEFAUT)
    )


# ============================================================================
# SCORING ENGINE
# ============================================================================

class ScoringEngine:
    """
    Moteur de scoring independant.
    
    Utilisation :
        engine = ScoringEngine()
        result = engine.diagnoser(config, valeurs_client)
    """
    
    def __init__(self, benchmarks: Optional[dict] = None):
        """
        Args:
            benchmarks: Dictionnaire de benchmarks sectoriels.
                       Si None, charge benchmarks.json par defaut.
        """
        if benchmarks is None:
            benchmarks = self._charger_benchmarks_defaut()
        self.benchmarks = benchmarks
        self.indicateurs = self._construire_indicateurs()
    
    def _charger_benchmarks_defaut(self) -> dict:
        """Charge les benchmarks depuis benchmarks.json."""
        path = os.path.join(os.path.dirname(__file__), "benchmarks.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._benchmarks_fallback()
    
    def _benchmarks_fallback(self) -> dict:
        """Benchmarks hardcodes en fallback (meme valeurs que l'ancien code)."""
        return {
            "Industrie": {
                "T01": 6.0, "T02": 1.2, "T03": 80, "T04": 25, "T05": 95,
                "T06": 15, "T07": 25, "T08": 85, "T09": 2,
                "M01": 15, "M02": 8, "M03": 2, "M04": 0.12, "M05": 0.05,
                "M06": 0.02, "M07": 0.80, "M08": 100, "M09": 25, "M10": 15,
                "M11": 550, "M12": 2, "M13": 7,
                "S01": 60, "S02": 6, "S03": 5, "S04": 3, "S05": 2,
                "S06": 80, "S07": 1.5,
                "E01": 85, "E02": 6, "E03": 1.2, "E04": 25, "E05": 0.5,
                "E06": 75,
                "P01": 5, "P02": 70, "P03": 1.0, "P04": 0.5,
                "A01": 80, "A02": 60, "A03": 92, "A04": 30,
            },
            "E-commerce": {
                "T01": 12.0, "T02": 1.8, "T03": 65, "T04": 10, "T05": 92,
                "T06": 25, "T07": 35, "T08": 120, "T09": 4,
                "M01": 2, "M02": 15, "M03": 5, "M04": 0.18, "M05": 0.08,
                "M06": 0.04, "M07": 1.20, "M08": 120, "M09": 30, "M10": 20,
                "M11": 650, "M12": 1, "M13": 5,
                "S01": 45, "S02": 8, "S03": 8, "S04": 5, "S05": 4,
                "S06": 75, "S07": 1.0,
                "E01": 90, "E02": 12, "E03": 1.8, "E04": 40, "E05": 1.0,
                "E06": 85,
                "P01": 2, "P02": 85, "P03": 2.0, "P04": 1.5,
                "A01": 70, "A02": 30, "A03": 88, "A04": 40,
            },
            "Distribution": {
                "T01": 4.0, "T02": 1.0, "T03": 85, "T04": 30, "T05": 96,
                "T06": 10, "T07": 20, "T08": 75, "T09": 1.5,
                "M01": 10, "M02": 5, "M03": 1, "M04": 0.10, "M05": 0.04,
                "M06": 0.015, "M07": 0.70, "M08": 95, "M09": 22, "M10": 12,
                "M11": 500, "M12": 2, "M13": 6,
                "S01": 35, "S02": 10, "S03": 3, "S04": 2, "S05": 2,
                "S06": 85, "S07": 0.8,
                "E01": 80, "E02": 5, "E03": 0.9, "E04": 35, "E05": 0.3,
                "E06": 70,
                "P01": 3, "P02": 60, "P03": 0.5, "P04": 0.3,
                "A01": 85, "A02": 45, "A03": 95, "A04": 25,
            },
            "Agroalimentaire": {
                "T01": 8.0, "T02": 1.3, "T03": 80, "T04": 20, "T05": 94,
                "T06": 12, "T07": 22, "T08": 80, "T09": 2.5,
                "M01": 20, "M02": 3, "M03": 0.5, "M04": 0.14, "M05": 0.06,
                "M06": 0.025, "M07": 0.90, "M08": 110, "M09": 28, "M10": 18,
                "M11": 600, "M12": 1.5, "M13": 4,
                "S01": 30, "S02": 12, "S03": 6, "S04": 4, "S05": 3,
                "S06": 78, "S07": 1.2,
                "E01": 82, "E02": 7, "E03": 1.0, "E04": 30, "E05": 0.4,
                "E06": 80,
                "P01": 4, "P02": 65, "P03": 1.0, "P04": 0.8,
                "A01": 75, "A02": 50, "A03": 90, "A04": 35,
            },
            "Pharma": {
                "T01": 3.0, "T02": 1.5, "T03": 90, "T04": 35, "T05": 98,
                "T06": 8, "T07": 30, "T08": 95, "T09": 1,
                "M01": 5, "M02": 10, "M03": 8, "M04": 0.15, "M05": 0.07,
                "M06": 0.03, "M07": 1.00, "M08": 105, "M09": 27, "M10": 16,
                "M11": 580, "M12": 2, "M13": 8,
                "S01": 90, "S02": 4, "S03": 2, "S04": 1, "S05": 1,
                "S06": 90, "S07": 0.5,
                "E01": 88, "E02": 8, "E03": 1.3, "E04": 28, "E05": 0.2,
                "E06": 85,
                "P01": 3, "P02": 80, "P03": 0.5, "P04": 0.2,
                "A01": 90, "A02": 75, "A03": 96, "A04": 20,
            },
            "Luxe": {
                "T01": 4.0, "T02": 1.4, "T03": 75, "T04": 30, "T05": 97,
                "T06": 6, "T07": 28, "T08": 110, "T09": 1.5,
                "M01": 3, "M02": 12, "M03": 3, "M04": 0.13, "M05": 0.06,
                "M06": 0.03, "M07": 1.10, "M08": 100, "M09": 25, "M10": 14,
                "M11": 550, "M12": 1.5, "M13": 6,
                "S01": 180, "S02": 2, "S03": 3, "S04": 2, "S05": 2,
                "S06": 88, "S07": 0.6,
                "E01": 80, "E02": 15, "E03": 1.5, "E04": 22, "E05": 0.3,
                "E06": 70,
                "P01": 2, "P02": 75, "P03": 0.5, "P04": 0.3,
                "A01": 80, "A02": 90, "A03": 94, "A04": 25,
            },
            "Automobile": {
                "T01": 5.0, "T02": 1.1, "T03": 85, "T04": 30, "T05": 96,
                "T06": 20, "T07": 24, "T08": 90, "T09": 2,
                "M01": 12, "M02": 6, "M03": 2, "M04": 0.11, "M05": 0.05,
                "M06": 0.02, "M07": 0.85, "M08": 98, "M09": 24, "M10": 13,
                "M11": 520, "M12": 2, "M13": 7,
                "S01": 45, "S02": 8, "S03": 4, "S04": 3, "S05": 2,
                "S06": 82, "S07": 1.0,
                "E01": 85, "E02": 7, "E03": 1.1, "E04": 30, "E05": 0.4,
                "E06": 80,
                "P01": 4, "P02": 70, "P03": 1.0, "P04": 0.5,
                "A01": 85, "A02": 55, "A03": 93, "A04": 30,
            },
        }
    
    def _construire_indicateurs(self) -> list[Indicateur]:
        """Construit la liste des 40 indicateurs."""
        return [
            # TRANSPORT (9 indicateurs standard)
            Indicateur("T01", "Cout transport / CA (%)", Domaine.TRANSPORT, "%", 5.0, 0.04, CritereScoring.MIN, 9),
            Indicateur("T02", "Cout EUR/km moyen", Domaine.TRANSPORT, "EUR", 1.2, 0.03, CritereScoring.MIN, 10),
            Indicateur("T03", "Taux chargement aller (%)", Domaine.TRANSPORT, "%", 80, 0.04, CritereScoring.MAX, 11),
            Indicateur("T04", "Taux chargement retour (%)", Domaine.TRANSPORT, "%", 25, 0.03, CritereScoring.MAX, 12),
            Indicateur("T05", "Taux OTIF transport (%)", Domaine.TRANSPORT, "%", 95, 0.04, CritereScoring.MAX, 13),
            Indicateur("T06", "Nombre de carriers", Domaine.TRANSPORT, "nb", 10, 0.02, CritereScoring.MIN, 14),
            Indicateur("T07", "Cout EUR/palette (national)", Domaine.TRANSPORT, "EUR", 25, 0.02, CritereScoring.MIN, 12),
            Indicateur("T08", "Cout EUR/palette (international)", Domaine.TRANSPORT, "EUR", 85, 0.02, CritereScoring.MIN, 13),
            Indicateur("T09", "Taux litiges transport (%)", Domaine.TRANSPORT, "%", 2, 0.02, CritereScoring.MIN, 14),
            # TRANSPORT MULTIMODAL (13 indicateurs)
            Indicateur("M01", "Part modale ferroviaire (%)", Domaine.TRANSPORT, "%", 15, 0.01, CritereScoring.MAX, 15),
            Indicateur("M02", "Part modale maritime (%)", Domaine.TRANSPORT, "%", 8, 0.01, CritereScoring.MAX, 16),
            Indicateur("M03", "Part modale aerien (%)", Domaine.TRANSPORT, "%", 2, 0.01, CritereScoring.MIN, 17),
            Indicateur("M04", "Cout EUR/tonne.km (route)", Domaine.TRANSPORT, "EUR/t.km", 0.12, 0.01, CritereScoring.MIN, 18),
            Indicateur("M05", "Cout EUR/tonne.km (fer)", Domaine.TRANSPORT, "EUR/t.km", 0.05, 0.01, CritereScoring.MIN, 19),
            Indicateur("M06", "Cout EUR/tonne.km (mer)", Domaine.TRANSPORT, "EUR/t.km", 0.02, 0.01, CritereScoring.MIN, 20),
            Indicateur("M07", "Cout EUR/tonne.km (air)", Domaine.TRANSPORT, "EUR/t.km", 0.80, 0.01, CritereScoring.MIN, 21),
            Indicateur("M08", "CO2 g/tonne.km (route)", Domaine.TRANSPORT, "g/t.km", 100, 0.01, CritereScoring.MIN, 22),
            Indicateur("M09", "CO2 g/tonne.km (fer)", Domaine.TRANSPORT, "g/t.km", 25, 0.01, CritereScoring.MIN, 23),
            Indicateur("M10", "CO2 g/tonne.km (mer)", Domaine.TRANSPORT, "g/t.km", 15, 0.01, CritereScoring.MIN, 24),
            Indicateur("M11", "CO2 g/tonne.km (air)", Domaine.TRANSPORT, "g/t.km", 550, 0.01, CritereScoring.MIN, 25),
            Indicateur("M12", "Delai livraison (j) route", Domaine.TRANSPORT, "j", 2, 0.01, CritereScoring.MIN, 26),
            Indicateur("M13", "Delai livraison (j) multimodal", Domaine.TRANSPORT, "j", 7, 0.01, CritereScoring.MIN, 27),
            # STOCKS (7 indicateurs)
            Indicateur("S01", "DSI (jours)", Domaine.STOCKS, "j", 45, 0.04, CritereScoring.MIN, 28),
            Indicateur("S02", "Taux rotation stock (x/an)", Domaine.STOCKS, "x/an", 8, 0.03, CritereScoring.MAX, 29),
            Indicateur("S03", "Stock dormant > 6 mois (%)", Domaine.STOCKS, "%", 10, 0.04, CritereScoring.MIN, 30),
            Indicateur("S04", "Taux d obsolescence (%)", Domaine.STOCKS, "%", 5, 0.03, CritereScoring.MIN, 31),
            Indicateur("S05", "Taux de rupture (%)", Domaine.STOCKS, "%", 2, 0.04, CritereScoring.MIN, 32),
            Indicateur("S06", "Forecast accuracy (%)", Domaine.STOCKS, "%", 85, 0.03, CritereScoring.MAX, 33),
            Indicateur("S07", "Cout detention stock (% CA)", Domaine.STOCKS, "% CA", 15, 0.02, CritereScoring.MIN, 34),
            # ENTREPOT (6 indicateurs)
            Indicateur("E01", "Taux occupation surface (%)", Domaine.ENTREPOT, "%", 85, 0.03, CritereScoring.MAX, 35),
            Indicateur("E02", "Cout m2/mois (EUR)", Domaine.ENTREPOT, "EUR/m2", 35, 0.03, CritereScoring.MIN, 36),
            Indicateur("E03", "Cout / ligne preparee (EUR)", Domaine.ENTREPOT, "EUR/ligne", 2.5, 0.04, CritereScoring.MIN, 37),
            Indicateur("E04", "Commandes / heure / ETP", Domaine.ENTREPOT, "nb", 25, 0.03, CritereScoring.MAX, 38),
            Indicateur("E05", "Taux erreur picking (%)", Domaine.ENTREPOT, "%", 0.3, 0.03, CritereScoring.MIN, 39),
            Indicateur("E06", "Hauteur utilisee (%)", Domaine.ENTREPOT, "%", 90, 0.02, CritereScoring.MAX, 40),
            # PROCESSUS (4 indicateurs)
            Indicateur("P01", "Delai order-to-cash (j)", Domaine.PROCESSUS, "j", 48, 0.03, CritereScoring.MIN, 41),
            Indicateur("P02", "Commandes automatisees (%)", Domaine.PROCESSUS, "%", 80, 0.03, CritereScoring.MAX, 42),
            Indicateur("P03", "Taux erreur facturation (%)", Domaine.PROCESSUS, "%", 0.5, 0.02, CritereScoring.MIN, 43),
            Indicateur("P04", "Taux d avoirs / CA (%)", Domaine.PROCESSUS, "%", 1.0, 0.02, CritereScoring.MIN, 44),
            # ACHATS (4 indicateurs)
            Indicateur("A01", "Fournisseurs sous contrat (%)", Domaine.ACHATS, "%", 80, 0.02, CritereScoring.MAX, 45),
            Indicateur("A02", "DPO (jours)", Domaine.ACHATS, "j", 60, 0.02, CritereScoring.MAX, 46),
            Indicateur("A03", "OTIF fournisseurs (%)", Domaine.ACHATS, "%", 95, 0.02, CritereScoring.MAX, 47),
            Indicateur("A04", "Dependance Top 5 fournisseurs (%)", Domaine.ACHATS, "%", 40, 0.02, CritereScoring.MIN, 48),
        ]
    
    def get_benchmark(self, code: str, secteur: str) -> float:
        """Recupere le benchmark pour un indicateur et un secteur."""
        sector_benchmarks = self.benchmarks.get(secteur, self.benchmarks.get("Industrie", {}))
        return sector_benchmarks.get(code, 0.0)
    
    def calculer_note(self, valeur: float, benchmark: float, critere: CritereScoring, seuils: dict) -> int:
        """
        Calcule la note /10 pour un indicateur.
        
        Logique :
            MIN (cout, delai) : plus bas = mieux
                valeur <= benchmark → 10
                valeur <= benchmark * 1.2 → 7
                valeur <= benchmark * 1.5 → 4
                sinon → 1
            
            MAX (taux, rotation) : plus haut = mieux
                valeur >= benchmark → 10
                valeur >= benchmark * 0.8 → 7
                valeur >= benchmark * 0.5 → 4
                sinon → 1
        """
        if benchmark == 0:
            return 5  # Pas de reference → note neutre
        
        if critere == CritereScoring.MIN:
            if valeur <= benchmark:
                return seuils["note_max"]
            elif valeur <= benchmark * seuils["seuil_jaune"]:
                return 7
            elif valeur <= benchmark * seuils["seuil_orange"]:
                return 4
            else:
                return 1
        else:  # MAX
            if valeur >= benchmark:
                return seuils["note_max"]
            elif valeur >= benchmark * (2 - seuils["seuil_jaune"]):
                return 7
            elif valeur >= benchmark * (2 - seuils["seuil_orange"]):
                return 4
            else:
                return 1
    
    def calculer_ecart(self, valeur: float, benchmark: float, critere: CritereScoring) -> float:
        """Calcule l'ecart en pourcentage entre la valeur et le benchmark."""
        if benchmark == 0:
            return 0.0
        if critere == CritereScoring.MIN:
            return (valeur - benchmark) / benchmark
        else:
            return (benchmark - valeur) / benchmark
    
    def scorer_indicateur(
        self, indicateur: Indicateur, valeur_client: float, secteur: str, config: ConfigMission
    ) -> ResultatIndicateur:
        """Score un seul indicateur."""
        benchmark = self.get_benchmark(indicateur.code, secteur)
        ecart = self.calculer_ecart(valeur_client, benchmark, indicateur.critere)
        note = self.calculer_note(valeur_client, benchmark, indicateur.critere, config.seuils)
        poids_domaine = config.ponderations.get(indicateur.domaine, 0.1)
        score_pondere = note * poids_domaine * indicateur.poids * 100  # Normalise
        
        # Statut
        if note >= 7:
            statut = "optimal" if note == 10 else "correct"
        elif note >= 4:
            statut = "attention"
        else:
            statut = "critique"
        
        return ResultatIndicateur(
            indicateur=indicateur,
            valeur_client=valeur_client,
            benchmark=benchmark,
            ecart_pct=ecart,
            note=note,
            score_pondere=score_pondere,
            statut=statut,
        )
    
    def diagnoser(
        self, config: ConfigMission, valeurs: dict[str, float]
    ) -> DiagnosticComplet:
        """
        Lance un diagnostic complet.
        
        Args:
            config: Parametres de la mission
            valeurs: Dict code_indicateur → valeur_client
        
        Returns:
            DiagnosticComplet avec tous les scores
        """
        resultats_domaines: dict[Domaine, list[ResultatIndicateur]] = {
            d: [] for d in Domaine
        }
        
        for indicateur in self.indicateurs:
            valeur = valeurs.get(indicateur.code, 0.0)
            if valeur == 0.0:
                continue  # Indicateur non saisi
            resultat = self.scorer_indicateur(indicateur, valeur, config.secteur, config)
            resultats_domaines[indicateur.domaine].append(resultat)
        
        # Agregation par domaine
        domaines = {}
        for domaine, resultats in resultats_domaines.items():
            if not resultats:
                continue
            poids = config.ponderations.get(domaine, 0.1)
            score_brut = sum(r.note * r.indicateur.poids for r in resultats) / sum(r.indicateur.poids for r in resultats)
            score_pondere = score_brut  # Sur echelle 0-10
            nb_critiques = sum(1 for r in resultats if r.statut == "critique")
            domaines[domaine] = ResultatDomaine(
                domaine=domaine,
                score=round(score_pondere, 2),
                nb_indicateurs=len(resultats),
                nb_critiques=nb_critiques,
                indicateurs=resultats,
            )
        
        # Score global (moyenne ponderee par les poids de domaines)
        score_global = 0.0
        poids_total = 0.0
        for domaine, res in domaines.items():
            poids = config.ponderations.get(domaine, 0.1)
            score_global += res.score * poids
            poids_total += poids
        if poids_total > 0:
            score_global /= poids_total
        
        # Calcul des fuites (simplifie)
        fuite_totale = self._calculer_fuites(config, valeurs)
        fuite_pct = fuite_totale / config.ca_annuel_ht if config.ca_annuel_ht > 0 else 0.0
        
        nb_total = sum(d.nb_indicateurs for d in domaines.values())
        nb_critiques = sum(d.nb_critiques for d in domaines.values())
        nb_quick_wins = sum(
            1 for d in domaines.values()
            for r in d.indicateurs
            if r.statut in ("critique", "attention") and r.indicateur.poids >= 0.03
        )
        
        return DiagnosticComplet(
            score_global=round(score_global, 2),
            domaines=domaines,
            fuite_totale_eur=round(fuite_totale, 0),
            fuite_pct_ca=round(fuite_pct, 4),
            nb_indicateurs=nb_total,
            nb_critiques=nb_critiques,
            nb_quick_wins=nb_quick_wins,
        )
    
    def _calculer_fuites(self, config: ConfigMission, valeurs: dict[str, float]) -> float:
        """Estime les fuites totales en EUR (formule simplifiee)."""
        fuites = {
            "T01": lambda v, b: max(0, v - b) / 100 * config.ca_annuel_ht,
            "T02": lambda v, b: max(0, v - b) * 100000,  # ~100k km
            "T05": lambda v, b: max(0, b - v) / 100 * config.ca_annuel_ht * 0.05,
            "S01": lambda v, b: max(0, v - b) / 365 * config.ca_annuel_ht * 0.15,
            "S03": lambda v, b: max(0, v - b) / 100 * config.ca_annuel_ht * 0.10,
            "S05": lambda v, b: max(0, v - b) / 100 * config.ca_annuel_ht * 0.05,
            "E03": lambda v, b: max(0, v - b) * 50000,  # ~50k lignes/an
            "E05": lambda v, b: max(0, v - b) / 100 * config.ca_annuel_ht * 0.02,
            "P03": lambda v, b: max(0, v - b) / 100 * config.ca_annuel_ht * 0.03,
            "A03": lambda v, b: max(0, b - v) / 100 * config.ca_annuel_ht * 0.04,
        }
        total = 0.0
        for code, calculer in fuites.items():
            v = valeurs.get(code, 0.0)
            b = self.get_benchmark(code, config.secteur)
            if v > 0:
                total += calculer(v, b)
        return total
    
    def get_indicateurs_par_domaine(self, domaine: Domaine) -> list[Indicateur]:
        """Retourne les indicateurs d'un domaine."""
        return [i for i in self.indicateurs if i.domaine == domaine]
    
    def get_liste_secteurs(self) -> list[str]:
        """Retourne la liste des secteurs disponibles."""
        return list(self.benchmarks.keys())


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def format_eur(montant: float) -> str:
    """Formate un montant en EUR."""
    return f"{montant:,.0f} EUR".replace(",", " ")

def format_pct(valeur: float) -> str:
    """Formate un pourcentage."""
    return f"{valeur:.1f}%"

def statut_emoji(note: int) -> str:
    """Retourne un indicateur visuel pour une note."""
    if note >= 7:
        return "[VERT]" if note == 10 else "[JAUNE]"
    elif note >= 4:
        return "[ORANGE]"
    else:
        return "[ROUGE]"


# ============================================================================
# MAIN (test rapide)
# ============================================================================

if __name__ == "__main__":
    print(f"Scoring Engine v{ENGINE_VERSION}")
    print(f"Secteurs disponibles : {ScoringEngine().get_liste_secteurs()}")
    
    # Test rapide
    engine = ScoringEngine()
    config = ConfigMission(nom_entreprise="TEST", secteur="E-commerce", ca_annuel_ht=28_000_000)
    
    # Valeurs de test (mauvaises performances)
    valeurs_test = {
        "T01": 14.0, "T02": 1.6, "T03": 60, "T04": 8, "T05": 88,
        "S01": 50, "S02": 6, "S03": 12, "S04": 7, "S05": 6, "S06": 65, "S07": 1.5,
        "E03": 2.0, "E05": 1.5,
    }
    
    result = engine.diagnoser(config, valeurs_test)
    print(f"\nScore global : {result.score_global}/10")
    print(f"Fuite totale : {format_eur(result.fuite_totale_eur)} ({format_pct(result.fuite_pct_ca * 100)} du CA)")
    print(f"Nb indicateurs : {result.nb_indicateurs}")
    print(f"Nb critiques : {result.nb_critiques}")
    print(f"Nb quick wins : {result.nb_quick_wins}")
    
    for domaine, res in result.domaines.items():
        print(f"\n  {domaine.value}: {res.score}/10 ({res.nb_indicateurs} indicateurs, {res.nb_critiques} critiques)")
        for r in res.indicateurs:
            print(f"    {statut_emoji(r.note)} {r.indicateur.code}: {r.valeur_client} vs {r.benchmark} -> note {r.note}/10")
