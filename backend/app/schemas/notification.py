from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    kind: str
    read: bool = False
    payload: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationMarkRead(BaseModel):
    notification_ids: list[str] = []
    mark_all: bool = False
