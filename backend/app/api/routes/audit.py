from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.domain.enums import RoleName
from app.models.entities import AuditEvent, User

router = APIRouter()


@router.get("")
def list_audit_events(
    action: str | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.AUDITOR, RoleName.ADMIN)),
):
    q = db.query(AuditEvent)
    if action:
        q = q.filter(AuditEvent.action == action)
    if entity:
        q = q.filter(AuditEvent.entity == entity)
    if entity_id:
        q = q.filter(AuditEvent.entity_id == entity_id)
    if actor_id:
        q = q.filter(AuditEvent.actor_id == actor_id)

    total = q.count()
    items = q.order_by(AuditEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": e.id,
                "actor_id": e.actor_id,
                "actor_role": e.actor_role,
                "action": e.action,
                "entity": e.entity,
                "entity_id": e.entity_id,
                "previous_state": e.previous_state,
                "new_state": e.new_state,
                "reason": e.reason,
                "ip": e.ip,
                "policy_version": e.policy_version,
                "model_version": e.model_version,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{entity}/{entity_id}")
def entity_audit_history(entity: str, entity_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    events = db.query(AuditEvent).filter(AuditEvent.entity == entity, AuditEvent.entity_id == entity_id).order_by(AuditEvent.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "actor_id": e.actor_id,
            "action": e.action,
            "previous_state": e.previous_state,
            "new_state": e.new_state,
            "reason": e.reason,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
