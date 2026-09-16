from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    role: str = "applicant"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)
