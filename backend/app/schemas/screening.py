from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ScreeningResultOut(BaseModel):
    id: str
    application_id: str
    kind: str
    matched: bool
    score: float
    list_name: str | None = None
    matched_name: str | None = None
    is_simulated: bool = True
    payload: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScreeningTriggerRequest(BaseModel):
    application_id: str
