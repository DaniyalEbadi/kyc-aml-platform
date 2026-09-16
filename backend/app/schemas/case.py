from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CaseOut(BaseModel):
    id: str
    case_number: str
    application_id: str
    customer_id: str
    status: str
    priority: str
    risk_level: str
    assigned_to: str | None = None
    sla_hours: int = 48
    sla_due_at: datetime | None = None
    decision: str | None = None
    decision_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    customer_name: str = ""
    application_number: str = ""

    model_config = {"from_attributes": True}


class CaseAssignRequest(BaseModel):
    user_id: str


class CaseReviewRequest(BaseModel):
    action: str
    reason: str


class CaseUpdateRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None


class CaseListParams(BaseModel):
    status: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    assigned_to: str | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 20
