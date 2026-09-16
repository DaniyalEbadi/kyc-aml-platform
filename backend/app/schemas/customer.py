from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    first_name: str = Field(max_length=120)
    last_name: str = Field(max_length=120)
    national_id: str | None = Field(None, max_length=20)
    passport_number: str | None = Field(None, max_length=40)
    birth_date: str | None = Field(None, max_length=16)
    gender: str | None = Field(None, max_length=16)
    nationality: str = Field("ایران", max_length=80)
    province: str | None = Field(None, max_length=80)
    city: str | None = Field(None, max_length=80)
    address: str | None = None
    phone: str | None = Field(None, max_length=32)
    email: str | None = Field(None, max_length=255)


class CustomerUpdate(BaseModel):
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


class CustomerOut(BaseModel):
    id: str
    user_id: str | None = None
    first_name: str
    last_name: str
    national_id: str | None = None
    passport_number: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    nationality: str
    province: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    overall_risk_score: int = 0
    overall_risk_level: str = "low"
    created_at: datetime | None = None
    application_count: int = 0

    model_config = {"from_attributes": True}


class CustomerNoteCreate(BaseModel):
    body: str


class CustomerNoteOut(BaseModel):
    id: str
    customer_id: str
    author_id: str | None = None
    body: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
