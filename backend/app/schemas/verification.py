from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class VerificationOut(BaseModel):
    id: str
    application_id: str
    kind: str
    status: str
    score: float | None = None
    details: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FaceVerificationOut(BaseModel):
    id: str
    application_id: str
    similarity: float
    quality_score: float
    confidence: float
    decision: str
    reasons: list | None = None
    liveness_ready: bool = True
    is_simulated: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FaceCompareRequest(BaseModel):
    application_id: str
