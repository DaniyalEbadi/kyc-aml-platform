from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    application_id: str
    customer_id: str
    doc_type: str
    status: str
    original_filename: str
    content_type: str
    size_bytes: int
    is_simulated: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ExtractedFieldOut(BaseModel):
    id: str
    document_id: str
    field_name: str
    field_label: str
    value: str | None = None
    confidence: float = 0
    confirmed: bool = False

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    fields: list[ExtractedFieldOut] = []
    versions: list = []


class QualityReportOut(BaseModel):
    overall: float
    blur: float
    glare: float
    brightness: float
    contrast: float
    crop: float
    corners: float
    resolution: float
    rotation: float
    readability: float
    reasons: list[str]
    is_simulated: bool
