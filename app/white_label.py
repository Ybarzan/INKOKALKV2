"""
Systeme White-Label.
====================
Permet aux consultants de personnaliser le rapport avec leur marque.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass
class BrandConfig:
    """Configuration de marque pour le white-label."""
    # Identite
    nom_consultant: str = "SC&T Consulting"
    slogan: str = "Supply Chain Intelligence"
    
    # Couleurs (hex)
    primary_color: str = "#00d4aa"
    secondary_color: str = "#0099ff"
    dark_color: str = "#1a1a2e"
    text_color: str = "#333333"
    bg_color: str = "#ffffff"
    
    # Logo (URL ou chemin local)
    logo_url: str = ""
    logo_width: int = 200
    
    # Contact
    site_web: str = "https://sc-t-consulting.com"
    email: str = "contact@sc-t-consulting.com"
    telephone: str = ""
    
    # Options
    afficher_marque: bool = True
    afficher_coordonnees: bool = True
    footer_personnalise: str = ""


# Configuration par defaut
DEFAULT_BRAND = BrandConfig()


def charger_config(marque_id: str = "default") -> BrandConfig:
    """Charge une configuration de marque."""
    filepath = os.path.join(os.path.dirname(__file__), f"brand_{marque_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return BrandConfig(**data)
    return DEFAULT_BRAND


def sauvegarder_config(config: BrandConfig, marque_id: str = "default"):
    """Sauvegarde une configuration de marque."""
    filepath = os.path.join(os.path.dirname(__file__), f"brand_{marque_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "nom_consultant": config.nom_consultant,
            "slogan": config.slogan,
            "primary_color": config.primary_color,
            "secondary_color": config.secondary_color,
            "dark_color": config.dark_color,
            "text_color": config.text_color,
            "bg_color": config.bg_color,
            "logo_url": config.logo_url,
            "logo_width": config.logo_width,
            "site_web": config.site_web,
            "email": config.email,
            "telephone": config.telephone,
            "afficher_marque": config.afficher_marque,
            "afficher_coordonnees": config.afficher_coordonnees,
            "footer_personnalise": config.footer_personnalise,
        }, f, ensure_ascii=False, indent=2)


def generer_css(config: BrandConfig) -> str:
    """Genere le CSS customise pour le rapport."""
    return f"""
    :root {{
        --primary: {config.primary_color};
        --secondary: {config.secondary_color};
        --dark: {config.dark_color};
        --text: {config.text_color};
        --bg: {config.bg_color};
    }}
    """
