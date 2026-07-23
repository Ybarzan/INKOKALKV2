"""
Route /api/webhooks — Gestion des webhooks.
=============================================
Cree, liste et gere les webhooks (Zapier-compatible).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..webhooks import Webhook, EVENTS

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookCreateRequest(BaseModel):
    url: str = Field(..., description="URL du webhook")
    events: list[str] = Field(default=["diagnostic.created"], description="Evenements a ecouter")
    secret: str = Field(default="", description="Secret HMAC (optionnel)")


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: list[str]
    is_active: bool
    last_triggered: Optional[str] = None
    fail_count: int


@router.post("", response_model=dict)
def creer_webhook(
    req: WebhookCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cree un nouveau webhook."""
    # Valider les evenements
    for event in req.events:
        if event not in EVENTS:
            raise HTTPException(400, f"Evenement inconnu: {event}. Disponibles: {list(EVENTS.keys())}")

    webhook = Webhook(
        user_id=user.id,
        url=req.url,
        events=req.events,
        secret=req.secret or None,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return {
        "id": webhook.id,
        "url": webhook.url,
        "events": webhook.events,
        "message": "Webhook cree",
    }


@router.get("", response_model=list[WebhookResponse])
def lister_webhooks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste les webhooks de l'utilisateur."""
    whs = db.query(Webhook).filter(Webhook.user_id == user.id).all()
    return [
        WebhookResponse(
            id=w.id,
            url=w.url,
            events=w.events or [],
            is_active=w.is_active,
            last_triggered=w.last_triggered.isoformat() if w.last_triggered else None,
            fail_count=w.fail_count,
        )
        for w in whs
    ]


@router.delete("/{webhook_id}")
def supprimer_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Supprime un webhook."""
    wh = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == user.id,
    ).first()

    if not wh:
        raise HTTPException(404, "Webhook non trouve")

    db.delete(wh)
    db.commit()
    return {"success": True, "message": "Webhook supprime"}


@router.post("/{webhook_id}/toggle")
def toggle_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Active/desactive un webhook."""
    wh = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == user.id,
    ).first()

    if not wh:
        raise HTTPException(404, "Webhook non trouve")

    wh.is_active = not wh.is_active
    db.commit()
    return {"success": True, "is_active": wh.is_active}


@router.get("/events")
def lister_evenements():
    """Liste les evenements disponibles."""
    return {"events": EVENTS}
