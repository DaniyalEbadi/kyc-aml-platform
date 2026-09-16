from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class RiskAssessmentOut(BaseModel):
    id: str
    application_id: str
    score: int
    level: str
    recommended_decision: str
    explanation: str
    policy_version_id: str | None = None
    created_at: datetime | None = None
    factors: list["RiskFactorOut"] = []

    model_config = {"from_attributes": True}


class RiskFactorOut(BaseModel):
    id: str
    code: str
    label: str
    weight: int
    triggered: bool
    detail: str

    model_config = {"from_attributes": True}


class RiskReevaluateRequest(BaseModel):
    application_id: str
