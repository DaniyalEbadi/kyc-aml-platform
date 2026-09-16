from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.audit.service import write_audit
from app.core.config import settings
from app.core.errors import bad_request, forbidden, not_found
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.domain.enums import ApplicationStatus, DocumentType, OnboardingStep, RoleName
from app.integrations.storage import safe_filename, storage, virus_scan_hook
from app.models.entities import (
    Application,
    ApplicationEvent,
    Case,
    Customer,
    CustomerNote,
    Decision,
    Document,
    DocumentVersion,
    ExtractedField,
    FaceVerification,
    Job,
    Notification,
    Policy,
    PolicyChunk,
    PolicyVersion,
    RefreshToken,
    Review,
    RiskAssessment,
    ScreeningResult,
    User,
    Verification,
)
from app.workers.jobs import create_job, dispatch_document_job
from app.ai.vision import get_vision_provider
from app.integrations.storage import storage as file_storage
from app.rag.retriever import PolicyRetriever
from app.ai.llm import get_llm_provider
from app.models.entities import AIEvaluation


def authenticate(db: Session, email: str, password: str) -> tuple[User, str, str]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise bad_request("ایمیل یا گذرواژه نادرست است.")
    access = create_access_token(user.id)  # type: ignore[arg-type]
    refresh = create_refresh_token(user.id)  # type: ignore[arg-type]
    db.add(RefreshToken(user_id=user.id, token_hash=sha256(refresh.encode()).hexdigest()))
    db.commit()
    return user, access, refresh


def next_application_number(db: Session) -> str:
    n = db.query(func.count(Application.id)).scalar() or 0
    return f"APP-{1000 + n + 1}"


def create_onboarding(db: Session, user: User) -> Application:
    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if not customer:
        parts = user.full_name.split(" ", 1)
        customer = Customer(user_id=user.id, first_name=parts[0], last_name=parts[1] if len(parts) > 1 else "", email=user.email)
        db.add(customer)
        db.flush()
    app = Application(application_number=next_application_number(db), customer_id=customer.id, status=ApplicationStatus.DRAFT.value)
    db.add(app)
    db.flush()  # Flush to generate app.id
    db.add(ApplicationEvent(application_id=app.id, kind="created", message="درخواست پیش‌نویس ایجاد شد."))
    write_audit(db, action="application.create", entity="application", entity_id=app.id, actor_id=user.id, actor_role=user.role)
    db.commit()
    db.refresh(app)
    return app


def update_onboarding(db: Session, user: User, app_id: str, payload: dict) -> Application:
    app = db.get(Application, app_id)
    if not app:
        raise not_found("درخواست")
    customer = db.get(Customer, app.customer_id)
    if user.role == RoleName.APPLICANT.value and customer.user_id != user.id:
        raise forbidden()
    for key in ("first_name", "last_name", "national_id", "passport_number", "birth_date", "gender", "nationality", "province", "city", "address", "phone", "email"):
        if key in payload and payload[key] is not None:
            setattr(customer, key, payload[key])
    for key in ("source_of_funds", "occupation", "declared_income", "expected_volume", "jurisdiction", "current_step"):
        if key in payload and payload[key] is not None:
            setattr(app, key, payload[key])
    db.add(ApplicationEvent(application_id=app.id, kind="updated", message="اطلاعات درخواست به‌روزرسانی شد."))
    write_audit(db, action="application.update", entity="application", entity_id=app.id, actor_id=user.id, actor_role=user.role)
    db.commit()
    db.refresh(app)
    return app


def submit_application(db: Session, user: User, app_id: str) -> Application:
    app = db.get(Application, app_id)
    if not app:
        raise not_found("درخواست")
    app.status = ApplicationStatus.SUBMITTED.value
    app.submitted_at = datetime.now(timezone.utc)
    app.current_step = OnboardingStep.SUBMIT.value
    db.add(ApplicationEvent(application_id=app.id, kind="submitted", message="درخواست ارسال شد."))
    write_audit(db, action="application.submit", entity="application", entity_id=app.id, actor_id=user.id, actor_role=user.role)
    db.commit()
    from app.workers.pipeline import run_verification_suite
    customer = db.get(Customer, app.customer_id)
    run_verification_suite(db, app, customer)
    db.refresh(app)
    return app


def save_upload(db: Session, user: User, app_id: str, doc_type: str, upload, data: bytes) -> tuple[Document, Job]:
    app = db.get(Application, app_id)
    if not app:
        raise not_found("درخواست")
    virus_scan_hook(data)
    key = storage.save(upload, data)
    doc = Document(
        application_id=app.id,
        customer_id=app.customer_id,
        doc_type=doc_type,
        status="uploaded",
        original_filename=safe_filename(upload.filename or "upload"),
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=len(data),
        storage_key=key,
        is_simulated=settings.demo_mode,
    )
    db.add(doc)
    db.flush()
    db.add(DocumentVersion(document_id=doc.id, version=1, storage_key=key))
    job = create_job(db, "document_process", doc.id)
    db.commit()
    dispatch_document_job(job.id)
    db.refresh(doc)
    db.refresh(job)
    return doc, job


def compare_faces(db: Session, user: User, app_id: str, selfie_bytes: bytes, id_bytes: bytes | None) -> FaceVerification:
    provider = get_vision_provider(settings.vision_provider)
    result = provider.compare(id_bytes or b"id-placeholder", selfie_bytes)
    rec = FaceVerification(
        application_id=app_id,
        similarity=result.similarity,
        quality_score=result.quality_score,
        confidence=result.confidence,
        decision=result.decision,
        reasons=result.reasons,
        is_simulated=result.is_simulated,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def staff_can_access(user: User) -> bool:
    return user.role in {RoleName.ANALYST.value, RoleName.REVIEWER.value, RoleName.ADMIN.value, RoleName.AUDITOR.value}


def get_application_detail(db: Session, user: User, app_id: str) -> Application:
    app = db.get(Application, app_id)
    if not app:
        raise not_found("درخواست")
    customer = db.get(Customer, app.customer_id)
    if user.role == RoleName.APPLICANT.value and customer.user_id != user.id:
        raise forbidden()
    return app
