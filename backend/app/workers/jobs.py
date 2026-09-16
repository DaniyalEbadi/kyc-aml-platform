from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.enums import JobStatus
from app.models.entities import Job


def create_job(db: Session, kind: str, entity_id: str) -> Job:
    job = Job(kind=kind, status=JobStatus.QUEUED.value, entity_id=entity_id, stage="queued", progress=0)
    db.add(job)
    db.flush()
    return job


def update_job(db: Session, job: Job, *, status: str | None = None, progress: int | None = None, stage: str | None = None, error: str | None = None) -> None:
    if status:
        job.status = status
    if progress is not None:
        job.progress = progress
    if stage:
        job.stage = stage
    if error:
        job.error = error
    db.flush()


def dispatch_document_job(job_id: str) -> None:
    if settings.inline_jobs:
        from app.workers.pipeline import process_document_job

        process_document_job(job_id)
        return
    from app.workers.celery_app import process_document_task

    process_document_task.delay(job_id)
