from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery("kyc", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(name="process_document_task")
def process_document_task(job_id: str) -> None:
    from app.workers.pipeline import process_document_job

    process_document_job(job_id)
