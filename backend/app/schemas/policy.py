from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class PolicyOut(BaseModel):
    id: str
    code: str
    title: str
    created_at: datetime | None = None
    versions: list["PolicyVersionOut"] = []

    model_config = {"from_attributes": True}


class PolicyVersionOut(BaseModel):
    id: str
    policy_id: str
    version: str
    is_active: bool = True
    body: str
    created_at: datetime | None = None
    chunk_count: int = 0

    model_config = {"from_attributes": True}


class PolicyChunkOut(BaseModel):
    id: str
    version_id: str
    clause: str
    section: str
    text: str

    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    code: str
    title: str
    body: str
    version: str = "1.0"


class PolicySearchRequest(BaseModel):
    query: str
    top_k: int = 5
