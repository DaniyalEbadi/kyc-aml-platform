from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai.llm import get_llm_provider
from app.ai.ocr import get_ocr_provider, DocumentProcessor
from app.ai.vision import get_vision_provider
from app.aml.screening import get_screening_provider
from app.audit.service import write_audit
from app.core.config import settings
from app.db.session import SessionLocal
from app.documents.quality import analyze_image_bytes
from app.domain.decisions import decide
from app.domain.enums import ApplicationStatus, CasePriority, CaseStatus, DecisionCode, JobStatus, RiskLevel
from app.domain.risk import compute_risk
from app.domain.rules import validate_application_payload
from app.integrations.storage import storage
from app.models.entities import (
    AIEvaluation,
    Application,
    ApplicationEvent,
    Case,
    Customer,
    Decision,
    Document,
    ExtractedField,
    FaceVerification,
    Job,
    Notification,
    RiskAssessment,
    RiskFactor,
    ScreeningResult,
    User,
    Verification,
)
from app.rag.retriever import PolicyRetriever
from app.workers.jobs import update_job


def process_document_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return
        update_job(db, job, status=JobStatus.RUNNING.value, progress=10, stage="در حال پردازش...")
        doc = db.get(Document, job.entity_id)
        if not doc:
            update_job(db, job, status=JobStatus.FAILED.value, error="مدرک یافت نشد")
            db.commit()
            return
        app = db.get(Application, doc.application_id)
        customer = db.get(Customer, doc.customer_id)
        data = storage.read(doc.storage_key)
        update_job(db, job, progress=25, stage="بررسی کیفیت...")
        quality = analyze_image_bytes(data, doc.original_filename)
        processor = DocumentProcessor(get_ocr_provider(settings.ocr_provider))
        update_job(db, job, progress=50, stage="استخراج اطلاعات...")
        context = {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "national_id": customer.national_id,
            "birth_date": customer.birth_date,
            "gender": customer.gender,
            "nationality": customer.nationality,
            "address": customer.address,
            "passport_number": customer.passport_number,
        }
        ocr = processor.extract(data, doc.original_filename, doc.doc_type, context)
        db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).delete()
        for field in ocr.fields:
            db.add(
                ExtractedField(
                    document_id=doc.id,
                    field_name=field.field_name,
                    field_label=field.field_label,
                    value=field.value,
                    confidence=field.confidence,
                )
            )
        db.add(
            Verification(
                application_id=app.id,
                kind="ocr",
                status="done",
                score=sum(f.confidence for f in ocr.fields) / max(len(ocr.fields), 1),
                details={"quality": quality.to_dict(), "provider": ocr.provider, "is_simulated": ocr.is_simulated},
            )
        )
        doc.status = "processed"
        update_job(db, job, progress=70, stage="غربالگری و ریسک...")
        run_verification_suite(db, app, customer, quality_overall=quality.overall)
        update_job(db, job, status=JobStatus.SUCCEEDED.value, progress=100, stage="تکمیل شد")
        db.add(ApplicationEvent(application_id=app.id, kind="document_processed", message="پردازش مدرک تکمیل شد."))
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(Job, job_id)
        if job:
            update_job(db, job, status=JobStatus.FAILED.value, error="پردازش مدرک ناموفق بود.")
            db.commit()
        raise exc
    finally:
        db.close()


def _face_for_app(db: Session, application_id: str) -> FaceVerification | None:
    return (
        db.query(FaceVerification)
        .filter(FaceVerification.application_id == application_id)
        .order_by(FaceVerification.created_at.desc())
        .first()
    )


def run_verification_suite(db: Session, app: Application, customer: Customer, quality_overall: float = 80) -> dict:
    identity_fields = {}
    docs = db.query(Document).filter(Document.application_id == app.id).all()
    id_doc = next((d for d in docs if d.doc_type in {"passport", "national_id", "driver_license"}), None)
    addr_doc = next((d for d in docs if d.doc_type == "proof_of_address"), None)
    if id_doc:
        for f in id_doc.fields:
            identity_fields[f.field_name] = f.value
    payload = {
        "application_id": app.application_number,
        "customer_name": f"{customer.first_name} {customer.last_name}",
        "national_id": customer.national_id,
        "identity_document": {
            "name_on_document": identity_fields.get("first_name", customer.first_name)
            + " "
            + identity_fields.get("last_name", customer.last_name),
            "expiry_date": identity_fields.get("expiry_date"),
        },
        "proof_of_address": {"document_date": datetime.now(timezone.utc).date().isoformat()} if addr_doc else {},
        "quality": {"overall": quality_overall},
    }
    face = _face_for_app(db, app.id)
    if face:
        payload["face"] = {"similarity": face.similarity}

    screening_hits = get_screening_provider(settings.screening_provider).screen(
        f"{customer.first_name} {customer.last_name}", customer.national_id
    )
    db.query(ScreeningResult).filter(ScreeningResult.application_id == app.id).delete()
    pep = sanctions = False
    for hit in screening_hits:
        db.add(
            ScreeningResult(
                application_id=app.id,
                kind=hit.kind,
                matched=hit.matched,
                score=hit.score,
                list_name=hit.list_name,
                matched_name=hit.matched_name,
                is_simulated=hit.is_simulated,
                payload={"note": hit.note},
            )
        )
        if hit.kind == "pep" and hit.matched:
            pep = True
        if hit.kind == "sanctions" and hit.matched:
            sanctions = True

    bundle = validate_application_payload(payload)
    risk = compute_risk(
        bundle,
        quality_score=quality_overall,
        face_similarity=face.similarity if face else None,
        pep=pep,
        sanctions=sanctions,
        jurisdiction_risk=12 if customer.nationality != "ایران" else 8,
        declared_high_volume=app.expected_volume == "بالا",
    )
    assessment = RiskAssessment(
        application_id=app.id,
        score=risk.score,
        level=risk.level.value,
        recommended_decision=decide(bundle, risk.level, pep, sanctions).code.value,
        explanation="امتیاز ریسک توسط موتور قطعی محاسبه شد؛ مدل زبانی تصمیم‌گیر نیست.",
    )
    db.add(assessment)
    db.flush()
    for factor in risk.factors:
        db.add(
            RiskFactor(
                assessment_id=assessment.id,
                code=factor.code,
                label=factor.label,
                weight=factor.weight,
                triggered=factor.triggered,
                detail=factor.detail,
            )
        )

    outcome = decide(bundle, risk.level, pep, sanctions)
    policy_hits = PolicyRetriever().retrieve(db, "تصمیم احراز هویت مدرک منقضی ریسک بالا تحریم")
    llm = get_llm_provider(settings.llm_provider)
    system = "دستیار انطباق. هرگز خودت تأیید یا رد نهایی نکن. فقط توضیح بده."
    user_msg = (
        f"Decision computed by policy engine: {outcome.code.value}\n"
        f"Validation: {bundle.to_dict()}\n"
        f"Policy: {policy_hits}\n"
    )
    explanation = llm.generate(system, user_msg)
    db.add(
        AIEvaluation(
            application_id=app.id,
            model_name=settings.llm_provider,
            model_version="mock-1" if settings.llm_provider == "mock" else settings.claude_model,
            prompt_version="explain-v1",
            policy_version=policy_hits[0]["policy_version"] if policy_hits else None,
            retrieved_evidence=policy_hits,
            output=explanation,
            confidence=None,
        )
    )
    db.add(
        Decision(
            application_id=app.id,
            code=outcome.code.value,
            source="policy_engine",
            reason=outcome.reason,
            policy_clauses=policy_hits,
        )
    )
    apply_decision_to_application(db, app, customer, outcome, risk.level)
    write_audit(
        db,
        action="engine.decision",
        entity="application",
        entity_id=app.id,
        new_state={"decision": outcome.code.value, "risk": risk.level.value},
        reason=outcome.reason,
        policy_version=policy_hits[0]["policy_version"] if policy_hits else None,
        model_version="policy-engine-v1",
    )
    customer.overall_risk_score = risk.score
    customer.overall_risk_level = risk.level.value
    db.commit()
    return {"decision": outcome.code.value, "risk": risk.to_dict(), "explanation": explanation, "policy": policy_hits}


def apply_decision_to_application(db: Session, app: Application, customer: Customer, outcome, risk_level: RiskLevel) -> None:
    now = datetime.now(timezone.utc)
    if outcome.code == DecisionCode.APPROVED:
        app.status = ApplicationStatus.APPROVED.value
        app.decided_at = now
    elif outcome.code == DecisionCode.RESUBMISSION_REQUESTED:
        app.status = ApplicationStatus.NEEDS_RESUBMISSION.value
    else:
        app.status = ApplicationStatus.IN_REVIEW.value
        existing = db.query(Case).filter(Case.application_id == app.id, Case.status != CaseStatus.CLOSED.value).first()
        if not existing:
            seq = db.query(Case).count() + 1
            due = now + timedelta(hours=24 if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} else 48)
            case = Case(
                case_number=f"CASE-{seq:05d}",
                application_id=app.id,
                customer_id=customer.id,
                status=CaseStatus.OPEN.value,
                priority=CasePriority.CRITICAL.value if risk_level == RiskLevel.CRITICAL else CasePriority.HIGH.value if risk_level == RiskLevel.HIGH else CasePriority.NORMAL.value,
                risk_level=risk_level.value,
                sla_due_at=due,
            )
            db.add(case)
            reviewers = db.query(User).filter(User.role.in_(["reviewer", "analyst"])).all()
            for u in reviewers:
                db.add(
                    Notification(
                        user_id=u.id,
                        title="پرونده جدید برای بررسی",
                        body=f"درخواست {app.application_number} نیازمند بررسی انسانی است.",
                        kind="new_case",
                        payload={"application_id": app.id},
                    )
                )
            if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
                for u in reviewers:
                    db.add(
                        Notification(
                            user_id=u.id,
                            title="پرونده پرریسک",
                            body=f"سطح ریسک {risk_level.value} برای {app.application_number}",
                            kind="high_risk",
                        )
                    )
