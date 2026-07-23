"""
Route /api/brand — White-label.
================================
Personnalise le rapport avec la marque du consultant.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..auth import get_current_user
from ..models import User
from ..white_label import BrandConfig, charger_config, sauvegarder_config

router = APIRouter(prefix="/api/brand", tags=["brand"])


class BrandRequest(BaseModel):
    nom_consultant: str = Field(default="SC&T Consulting")
    slogan: str = Field(default="Supply Chain Intelligence")
    primary_color: str = Field(default="#00d4aa")
    secondary_color: str = Field(default="#0099ff")
    dark_color: str = Field(default="#1a1a2e")
    text_color: str = Field(default="#333333")
    bg_color: str = Field(default="#ffffff")
    logo_url: str = Field(default="")
    logo_width: int = Field(default=200)
    site_web: str = Field(default="")
    email: str = Field(default="")
    telephone: str = Field(default="")
    afficher_marque: bool = Field(default=True)
    afficher_coordonnees: bool = Field(default=True)
    footer_personnalise: str = Field(default="")


@router.get("")
def get_brand(
    marque_id: str = "default",
    user: User = Depends(get_current_user),
):
    """Recupere la configuration de marque."""
    config = charger_config(marque_id)
    return {
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
    }


@router.put("")
def update_brand(
    req: BrandRequest,
    marque_id: str = "default",
    user: User = Depends(get_current_user),
):
    """Met a jour la configuration de marque."""
    config = BrandConfig(
        nom_consultant=req.nom_consultant,
        slogan=req.slogan,
        primary_color=req.primary_color,
        secondary_color=req.secondary_color,
        dark_color=req.dark_color,
        text_color=req.text_color,
        bg_color=req.bg_color,
        logo_url=req.logo_url,
        logo_width=req.logo_width,
        site_web=req.site_web,
        email=req.email,
        telephone=req.telephone,
        afficher_marque=req.afficher_marque,
        afficher_coordonnees=req.afficher_coordonnees,
        footer_personnalise=req.footer_personnalise,
    )
    sauvegarder_config(config, marque_id)
    return {"success": True, "message": "Marque mise a jour"}


@router.get("/couleurs-preset")
def presets():
    """Retourne des presets de couleurs predefinis."""
    return {
        "presets": [
            {"nom": "Money Leak (defaut)", "primary": "#00d4aa", "secondary": "#0099ff", "dark": "#1a1a2e"},
            {"nom": "Orange Chaud", "primary": "#f97316", "secondary": "#fb923c", "dark": "#1c1917"},
            {"nom": "Bleu Pro", "primary": "#3b82f6", "secondary": "#60a5fa", "dark": "#1e3a5f"},
            {"nom": "Vert Nature", "primary": "#22c55e", "secondary": "#4ade80", "dark": "#14532d"},
            {"nom": "Rouge Premium", "primary": "#ef4444", "secondary": "#f87171", "dark": "#450a0a"},
            {"nom": "Violet Luxe", "primary": "#8b5cf6", "secondary": "#a78bfa", "dark": "#2e1065"},
            {"nom": "Neutre Pro", "primary": "#6b7280", "secondary": "#9ca3af", "dark": "#111827"},
        ]
    }
