from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User, Document
from app.services.kyc import save_upload

router = APIRouter()


@router.get("")
def list_documents(
    app_id: str | None = Query(None),
    customer_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Document)
    if app_id:
        q = q.filter(Document.application_id == app_id)
    if customer_id:
        q = q.filter(Document.customer_id == customer_id)
    docs = q.order_by(desc(Document.created_at)).all()
    return [
        {
            "id": d.id,
            "application_id": d.application_id,
            "customer_id": d.customer_id,
            "doc_type": d.doc_type,
            "status": d.status,
            "original_filename": d.original_filename,
            "content_type": d.content_type,
            "size_bytes": d.size_bytes,
            "is_simulated": d.is_simulated,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.post("/upload")
async def upload_document(
    app_id: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    doc, job = save_upload(db, user, app_id, doc_type, file, data)
    return {
        "document": {
            "id": doc.id,
            "doc_type": doc.doc_type,
            "status": doc.status,
            "original_filename": doc.original_filename,
            "size_bytes": doc.size_bytes,
        },
        "job": {
            "id": job.id,
            "status": job.status,
            "stage": job.stage,
        },
    }


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.entities import Document, ExtractedField
    doc = db.get(Document, document_id)
    if not doc:
        from app.core.errors import not_found
        raise not_found("مدرک")
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
    return {
        "id": doc.id,
        "application_id": doc.application_id,
        "customer_id": doc.customer_id,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "original_filename": doc.original_filename,
        "content_type": doc.content_type,
        "size_bytes": doc.size_bytes,
        "is_simulated": doc.is_simulated,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "fields": [
            {
                "id": f.id,
                "field_name": f.field_name,
                "field_label": f.field_label,
                "value": f.value,
                "confidence": f.confidence,
                "confirmed": f.confirmed,
            }
            for f in fields
        ],
    }


@router.get("/{document_id}/fields")
def get_document_fields(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.entities import ExtractedField
    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    return [
        {
            "id": f.id,
            "field_name": f.field_name,
            "field_label": f.field_label,
            "value": f.value,
            "confidence": f.confidence,
            "confirmed": f.confirmed,
        }
        for f in fields
    ]
