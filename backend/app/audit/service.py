from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.entities import AuditEvent


def write_audit(
    db: Session,
    *,
    action: str,
    entity: str,
    entity_id: str | None = None,
    actor_id: str | None = None,
    actor_role: str | None = None,
    previous_state: dict | None = None,
    new_state: dict | None = None,
    reason: str | None = None,
    request: Request | None = None,
    policy_version: str | None = None,
    model_version: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason,
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        policy_version=policy_version,
        model_version=model_version,
    )
    db.add(event)
    db.flush()
    return event
