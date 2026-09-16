from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class JobOut(BaseModel):
    id: str
    kind: str
    status: str
    progress: int = 0
    stage: str = ""
    entity_id: str | None = None
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
