from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class AuditEventOut(BaseModel):
    id: str
    actor_id: str | None = None
    actor_role: str | None = None
    action: str
    entity: str
    entity_id: str
    previous_state: dict | None = None
    new_state: dict | None = None
    reason: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    policy_version: str | None = None
    model_version: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditListParams(BaseModel):
    action: str | None = None
    entity: str | None = None
    entity_id: str | None = None
    actor_id: str | None = None
    page: int = 1
    page_size: int = 50
