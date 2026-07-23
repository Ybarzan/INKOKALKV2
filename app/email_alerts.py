"""
Systeme d'alertes email.
========================
Envoie des alertes quand des KPI sont critiques.
Supporte SMTP (Gmail, Outlook, etc.)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os


class AlertEmail:
    """
    Envoie des alertes email pour les KPI critiques.
    
    Utilisation :
        alerter = AlertEmail()
        alerter.envoyer_alerte(
            destinataire="client@example.com",
            score=4.2,
            critiques=["T01: 14% vs 6%", "S01: 50j vs 45j"],
        )
    """

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_pass: str = "",
        expediteur: str = "",
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_pass = smtp_pass or os.getenv("SMTP_PASS", "")
        self.expediteur = expediteur or os.getenv("SMTP_FROM", self.smtp_user)

    def _connecter(self) -> Optional[smtplib.SMTP]:
        """Connecte au serveur SMTP."""
        if not self.smtp_user or not self.smtp_pass:
            return None
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            return server
        except Exception as e:
            print(f"[ERREUR] SMTP: {e}")
            return None

    def envoyer_alerte(
        self,
        destinataire: str,
        score: float,
        critiques: list[str],
        fuite_eur: float = 0,
        secteur: str = "",
    ) -> bool:
        """Envoie une alerte email pour des KPI critiques."""
        server = self._connecter()
        if not server:
            print("[WARN] SMTP non configure — alerte non envoyee")
            return False

        # Couleur du score
        if score >= 7:
            score_color = "#22c55e"
            score_label = "Bon"
        elif score >= 4:
            score_color = "#eab308"
            score_label = "Attention"
        else:
            score_color = "#ef4444"
            score_label = "Critique"

        # Corps HTML
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">Money Leak Calculator</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.7;">Alerte Supply Chain</p>
            </div>
            
            <div style="padding: 20px; background: #f8fafc;">
                <h2>Alerte KPI Critique</h2>
                
                <div style="background: white; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid {score_color};">
                    <p style="margin: 0; font-size: 24px; font-weight: bold; color: {score_color};">
                        {score}/10 — {score_label}
                    </p>
                    <p style="margin: 5px 0 0 0; color: #666;">
                        {secteur} — Fuite estimee: {fuite_eur:,.0f} EUR
                    </p>
                </div>
                
                <h3>Indicateurs critiques :</h3>
                <ul>
                    {''.join(f'<li style="margin: 5px 0;">{c}</li>' for c in critiques)}
                </ul>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://moneyleak-api.onrender.com/docs" 
                       style="background: #00d4aa; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Voir le diagnostic
                    </a>
                </div>
            </div>
            
            <div style="background: #1a1a2e; color: #666; padding: 15px; text-align: center; font-size: 12px;">
                Money Leak Calculator — SC&T Consulting
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Money Leak] Alerte KPI — Score {score}/10"
        msg["From"] = self.expediteur
        msg["To"] = destinataire
        msg.attach(MIMEText(html, "html"))

        try:
            server.sendmail(self.expediteur, destinataire, msg.as_string())
            server.quit()
            print(f"[OK] Alerte envoyee a {destinataire}")
            return True
        except Exception as e:
            print(f"[ERREUR] Envoi email: {e}")
            server.quit()
            return False

    def envoyer_rapport(
        self,
        destinataire: str,
        score: float,
        fuite_eur: float,
        fuite_pct: float,
        nb_critiques: int,
        recommandations: list[str],
        secteur: str = "",
        nom_entreprise: str = "",
    ) -> bool:
        """Envoie le rapport complet par email."""
        server = self._connecter()
        if not server:
            return False

        recos_html = "".join(f"<li>{r}</li>" for r in recommandations[:10])

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #00d4aa, #0099ff); color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0;">Money Leak Calculator</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Rapport Diagnostic Supply Chain</p>
            </div>
            
            <div style="padding: 20px;">
                <h2>{nom_entreprise or 'Client'}</h2>
                <p>Secteur: {secteur}</p>
                
                <div style="display: flex; gap: 10px; margin: 20px 0;">
                    <div style="flex: 1; background: #f0fdf4; padding: 15px; border-radius: 8px; text-align: center;">
                        <p style="font-size: 28px; font-weight: bold; color: #22c55e; margin: 0;">{score}/10</p>
                        <p style="margin: 5px 0 0 0; color: #666;">Score</p>
                    </div>
                    <div style="flex: 1; background: #fef2f2; padding: 15px; border-radius: 8px; text-align: center;">
                        <p style="font-size: 28px; font-weight: bold; color: #ef4444; margin: 0;">{fuite_eur:,.0f} EUR</p>
                        <p style="margin: 5px 0 0 0; color: #666;">Fuite</p>
                    </div>
                </div>
                
                <h3>Recommandations :</h3>
                <ol>{recos_html}</ol>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://moneyleak-api.onrender.com/docs" 
                       style="background: #00d4aa; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                        Voir en ligne
                    </a>
                </div>
            </div>
            
            <div style="background: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                Money Leak Calculator — SC&T Consulting
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Money Leak] Rapport — {nom_entreprise or 'Diagnostic'}"
        msg["From"] = self.expediteur
        msg["To"] = destinataire
        msg.attach(MIMEText(html, "html"))

        try:
            server.sendmail(self.expediteur, destinataire, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"[ERREUR] Envoi rapport: {e}")
            server.quit()
            return False
