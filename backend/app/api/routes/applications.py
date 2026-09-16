from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.errors import not_found
from app.db.session import get_db
from app.domain.enums import ApplicationStatus, RoleName
from app.models.entities import Application, Customer, RiskAssessment, User
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut
from app.services.kyc import create_onboarding, update_onboarding, submit_application, get_application_detail

router = APIRouter()


@router.get("")
def list_applications(
    status: str | None = None,
    risk_level: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Application)
    if status:
        q = q.filter(Application.status == status)
    if search:
        q = q.join(Customer).filter(
            or_(
                Application.application_number.ilike(f"%{search}%"),
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
                Customer.national_id.ilike(f"%{search}%"),
            )
        )
    if risk_level:
        q = q.join(RiskAssessment).filter(RiskAssessment.level == risk_level)

    sort_col = getattr(Application, sort_by, Application.created_at)
    q = q.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for app in items:
        customer = db.get(Customer, app.customer_id)
        risk = db.query(RiskAssessment).filter(RiskAssessment.application_id == app.id).order_by(RiskAssessment.created_at.desc()).first()
        result.append({
            "id": app.id,
            "application_number": app.application_number,
            "customer_id": app.customer_id,
            "status": app.status,
            "source": app.source,
            "current_step": app.current_step,
            "jurisdiction": app.jurisdiction,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "decided_at": app.decided_at.isoformat() if app.decided_at else None,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "customer_name": f"{customer.first_name} {customer.last_name}" if customer else "",
            "risk_level": risk.level if risk else None,
            "risk_score": risk.score if risk else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.post("")
def create_application(body: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.APPLICANT, RoleName.ANALYST))):
    app = create_onboarding(db, user)
    return {
        "id": app.id,
        "application_number": app.application_number,
        "status": app.status,
    }


@router.get("/{app_id}")
def get_application(app_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    app = get_application_detail(db, user, app_id)
    customer = db.get(Customer, app.customer_id)
    risk = db.query(RiskAssessment).filter(RiskAssessment.application_id == app.id).order_by(RiskAssessment.created_at.desc()).first()
    from app.models.entities import Document, ApplicationEvent, ScreeningResult, Decision, Verification, Case, FaceVerification
    docs = db.query(Document).filter(Document.application_id == app.id).all()
    events = db.query(ApplicationEvent).filter(ApplicationEvent.application_id == app.id).order_by(ApplicationEvent.created_at.desc()).all()
    screenings = db.query(ScreeningResult).filter(ScreeningResult.application_id == app.id).all()
    decisions = db.query(Decision).filter(Decision.application_id == app.id).all()
    verifications = db.query(Verification).filter(Verification.application_id == app.id).all()
    cases = db.query(Case).filter(Case.application_id == app.id).all()
    face = db.query(FaceVerification).filter(FaceVerification.application_id == app.id).order_by(FaceVerification.created_at.desc()).first()

    return {
        "id": app.id,
        "application_number": app.application_number,
        "customer_id": app.customer_id,
        "status": app.status,
        "source": app.source,
        "current_step": app.current_step,
        "declared_income": app.declared_income,
        "source_of_funds": app.source_of_funds,
        "occupation": app.occupation,
        "expected_volume": app.expected_volume,
        "jurisdiction": app.jurisdiction,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "decided_at": app.decided_at.isoformat() if app.decided_at else None,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "customer_name": f"{customer.first_name} {customer.last_name}" if customer else "",
        "customer": {
            "id": customer.id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "national_id": customer.national_id,
            "passport_number": customer.passport_number,
            "birth_date": customer.birth_date,
            "gender": customer.gender,
            "nationality": customer.nationality,
            "phone": customer.phone,
            "email": customer.email,
        } if customer else None,
        "risk": {
            "id": risk.id,
            "score": risk.score,
            "level": risk.level,
            "recommended_decision": risk.recommended_decision,
            "explanation": risk.explanation,
            "factors": [
                {"code": f.code, "label": f.label, "weight": f.weight, "triggered": f.triggered, "detail": f.detail}
                for f in (risk.factors if risk else [])
            ],
        } if risk else None,
        "documents": [
            {"id": d.id, "doc_type": d.doc_type, "status": d.status, "original_filename": d.original_filename, "content_type": d.content_type, "size_bytes": d.size_bytes, "is_simulated": d.is_simulated, "created_at": d.created_at.isoformat() if d.created_at else None}
            for d in docs
        ],
        "events": [
            {"id": e.id, "kind": e.kind, "message": e.message, "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in events
        ],
        "screenings": [
            {"id": s.id, "kind": s.kind, "matched": s.matched, "score": s.score, "list_name": s.list_name, "matched_name": s.matched_name, "is_simulated": s.is_simulated}
            for s in screenings
        ],
        "decisions": [
            {"id": d.id, "code": d.code, "source": d.source, "reason": d.reason, "policy_clauses": d.policy_clauses, "created_at": d.created_at.isoformat() if d.created_at else None}
            for d in decisions
        ],
        "verifications": [
            {"id": v.id, "kind": v.kind, "status": v.status, "score": v.score, "details": v.details}
            for v in verifications
        ],
        "cases": [
            {"id": c.id, "case_number": c.case_number, "status": c.status, "priority": c.priority, "risk_level": c.risk_level}
            for c in cases
        ],
        "face_verification": {
            "id": face.id,
            "similarity": face.similarity,
            "quality_score": face.quality_score,
            "confidence": face.confidence,
            "decision": face.decision,
            "reasons": face.reasons,
            "is_simulated": face.is_simulated,
        } if face else None,
    }


@router.put("/{app_id}")
def update_application(app_id: str, body: ApplicationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    app = update_onboarding(db, user, app_id, body.model_dump(exclude_unset=True))
    return {"id": app.id, "status": app.status, "current_step": app.current_step}


@router.post("/{app_id}/submit")
def submit(app_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    app = submit_application(db, user, app_id)
    return {"id": app.id, "status": app.status}
