"""
Traductions FR/EN pour l'API Money Leak Calculator.
====================================================
Systeme simple de traduction par cle.
"""

# === TRADUCTIONS ===
TRANSLATIONS = {
    "fr": {
        # Auth
        "email_deja_utilise": "Cet email est deja utilise",
        "email_mdp_incorrect": "Email ou mot de passe incorrect",
        "compte_desactive": "Compte desactive",
        "token_invalide": "Token invalide ou expire",
        "utilisateur_non_trouve": "Utilisateur non trouve",
        "compte_cree": "Compte cree avec succes",
        "connexion_reussie": "Connexion reussie",

        # Diagnostic
        "diagnostic_non_trouve": "Diagnostic non trouve",
        "lancer_diagnostic": "Lancer un diagnostic complet",
        "aucun_indicateur_critique": "Aucun indicateur critique !",
        "excellentes_performances": "Excellentes performances ! Pas de fuite majeure detectee.",

        # Domaines
        "TRANSPORT": "Transport",
        "STOCKS": "Stocks",
        "ENTREPOT": "Entrepot",
        "PROCESSUS": "Processus",
        "ACHATS": "Achats",

        # Statuts
        "optimal": "Optimal",
        "correct": "Correct",
        "attention": "Attention",
        "critique": "Critique",

        # Recommandations
        "urgent": "URGENT",
        "amelioration_possible": "Des quick wins sont possibles",
        "potentiel_economie": "Potentiel d'economie estime",

        # Prediction
        "score_actuel": "Score actuel",
        "score_predit": "Score predit sur 3 mois",
        "gain_estime": "Gain estime",
        "economie_annuelle": "Economie annuelle estimee",

        # PDF
        "rapport_diagnostic": "Rapport de Diagnostic Supply Chain",
        "score_global": "Score Global",
        "fuite_totale": "Fuite totale estimee",
        "fuite_ca": "Fuite / CA",
        "indicateurs_analyses": "Indicateurs analyses",
        "indicateurs_critiques": "Indicateurs critiques",
        "quick_wins": "Quick wins identifies",
        "scores_domaine": "Scores par Domaine",
        "detail_indicateurs": "Detail des Indicateurs",
        "recommandations": "Recommandations",
        "rapport_genere": "Rapport genere le",

        # Packs
        "pack_fuite_scan": "Diagnostic flash des fuites de rentabilite",
        "pack_redesign_express": "Quick wins + projets structurants",
        "pack_redesign_total": "Transformation complete de la Supply Chain",
        "pack_transfert": "Formation + coaching des equipes",
    },

    "en": {
        # Auth
        "email_deja_utilise": "This email is already in use",
        "email_mdp_incorrect": "Incorrect email or password",
        "compte_desactive": "Account deactivated",
        "token_invalide": "Invalid or expired token",
        "utilisateur_non_trouve": "User not found",
        "compte_cree": "Account created successfully",
        "connexion_reussie": "Login successful",

        # Diagnostic
        "diagnostic_non_trouve": "Diagnostic not found",
        "lancer_diagnostic": "Run a full diagnostic",
        "aucun_indicateur_critique": "No critical indicators!",
        "excellentes_performances": "Excellent performance! No major leaks detected.",

        # Domaines
        "TRANSPORT": "Transport",
        "STOCKS": "Inventory",
        "ENTREPOT": "Warehouse",
        "PROCESSUS": "Process",
        "ACHATS": "Procurement",

        # Statuts
        "optimal": "Optimal",
        "correct": "Good",
        "attention": "Warning",
        "critique": "Critical",

        # Recommandations
        "urgent": "URGENT",
        "amelioration_possible": "Quick wins are possible",
        "potentiel_economie": "Estimated savings potential",

        # Prediction
        "score_actuel": "Current score",
        "score_predit": "Predicted score (3 months)",
        "gain_estime": "Estimated gain",
        "economie_annuelle": "Estimated annual savings",

        # PDF
        "rapport_diagnostic": "Supply Chain Diagnostic Report",
        "score_global": "Global Score",
        "fuite_totale": "Total estimated leak",
        "fuite_ca": "Leak / Revenue",
        "indicateurs_analyses": "Indicators analyzed",
        "indicateurs_critiques": "Critical indicators",
        "quick_wins": "Quick wins identified",
        "scores_domaine": "Domain Scores",
        "detail_indicateurs": "Indicator Details",
        "recommandations": "Recommendations",
        "rapport_genere": "Report generated on",

        # Packs
        "pack_fuite_scan": "Flash diagnostic of profitability leaks",
        "pack_redesign_express": "Quick wins + structuring projects",
        "pack_redesign_total": "Complete Supply Chain transformation",
        "pack_transfert": "Team training + coaching",
    },
}


def t(key: str, lang: str = "fr") -> str:
    """
    Traduit une cle dans la langue demandee.
    Si la cle n'existe pas, retourne la cle elle-meme.
    
    Utilisation :
        t("email_deja_utilise", "en")  → "This email is already in use"
        t("TRANSPORT", "fr")           → "Transport"
    """
    return TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, key)


def get_supported_languages() -> list[str]:
    """Retourne les langues supportees."""
    return list(TRANSLATIONS.keys())
