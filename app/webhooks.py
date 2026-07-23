"""
Systeme de Webhooks.
====================
Notifie les services externes quand un evenement se produit.
Zapier-compatible.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON
from datetime import datetime
import json
import urllib.request
import hashlib
import hmac

from .models import Base


class Webhook(Base):
    """Webhook enregistre par un utilisateur."""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)  # Pour verifier la signature
    events = Column(JSON, default=list)  # ["diagnostic.created", "alert.sent"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    fail_count = Column(Integer, default=0)


# Evenements disponibles
EVENTS = {
    "diagnostic.created": "Un nouveau diagnostic est cree",
    "diagnostic.completed": "Un diagnostic est termine",
    "alert.sent": "Une alerte email est envoyee",
    "rapport.generated": "Un rapport PDF est genere",
    "prediction.computed": "Une prediction est calculee",
}


def envoyer_webhook(
    url: str,
    event: str,
    data: dict,
    secret: str = None,
) -> bool:
    """
    Envoie un webhook a une URL.
    Format compatible Zapier/Make.
    """
    payload = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MoneyLeak-Webhook/1.0",
        "X-MoneyLeak-Event": event,
    }

    # Signature HMAC si secret fourni
    if secret:
        signature = hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        headers["X-MoneyLeak-Signature"] = f"sha256={signature}"

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception as e:
        print(f"[WARN] Webhook echoue: {url} — {e}")
        return False


def declencher_webhooks(
    db,
    user_id: int,
    event: str,
    data: dict,
):
    """Declenche tous les webhooks actifs pour un evenement."""
    webhooks = db.query(Webhook).filter(
        Webhook.user_id == user_id,
        Webhook.is_active == True,
    ).all()

    for wh in webhooks:
        if event in (wh.events or []):
            success = envoyer_webhook(wh.url, event, data, wh.secret)
            if success:
                wh.last_triggered = datetime.utcnow()
                wh.fail_count = 0
            else:
                wh.fail_count += 1
                if wh.fail_count >= 5:
                    wh.is_active = False  # Desactiver apres 5 echecs

    db.commit()
