from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    source: str = "web"
    jurisdiction: str = "ایران"


class ApplicationUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    national_id: str | None = None
    passport_number: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    nationality: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    source_of_funds: str | None = None
    occupation: str | None = None
    declared_income: str | None = None
    expected_volume: str | None = None
    jurisdiction: str | None = None
    current_step: str | None = None


class ApplicationOut(BaseModel):
    id: str
    application_number: str
    customer_id: str
    status: str
    source: str
    current_step: str
    declared_income: str | None = None
    source_of_funds: str | None = None
    occupation: str | None = None
    expected_volume: str | None = None
    jurisdiction: str
    submitted_at: datetime | None = None
    decided_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    customer_name: str = ""
    risk_level: str | None = None
    risk_score: int | None = None

    model_config = {"from_attributes": True}


class ApplicationDetailOut(ApplicationOut):
    documents: list = []
    events: list = []
    risk_assessments: list = []
    screenings: list = []
    decisions: list = []
    verifications: list = []
    cases: list = []


class ApplicationListParams(BaseModel):
    status: str | None = None
    risk_level: str | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
