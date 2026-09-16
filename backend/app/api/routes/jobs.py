from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import not_found
from app.db.session import get_db
from app.models.entities import Job, User

router = APIRouter()


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(Job, job_id)
    if not job:
        raise not_found("کار")
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "entity_id": job.entity_id,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }
