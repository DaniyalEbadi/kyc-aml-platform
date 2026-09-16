from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.entities import (
    Application, Customer, Case, RiskAssessment, ScreeningResult,
    Verification, Document, Decision, AuditEvent, User
)
from app.domain.enums import ApplicationStatus, RiskLevel, RoleName

router = APIRouter()


@router.get("")
def get_analytics(db: Session = Depends(get_db), _: User = Depends(require_roles(RoleName.ANALYST, RoleName.REVIEWER, RoleName.ADMIN))):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    total_apps = db.query(func.count(Application.id)).scalar() or 0
    new_apps = db.query(func.count(Application.id)).filter(Application.created_at >= seven_days_ago).scalar() or 0
    approved = db.query(func.count(Application.id)).filter(Application.status == ApplicationStatus.APPROVED.value).scalar() or 0
    rejected = db.query(func.count(Application.id)).filter(Application.status == ApplicationStatus.REJECTED.value).scalar() or 0
    in_review = db.query(func.count(Application.id)).filter(Application.status == ApplicationStatus.IN_REVIEW.value).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_cases = db.query(func.count(Case.id)).scalar() or 0
    open_cases = db.query(func.count(Case.id)).filter(Case.status.in_(["open", "assigned", "in_review"])).scalar() or 0
    high_risk = db.query(func.count(RiskAssessment.id)).filter(RiskAssessment.level == RiskLevel.HIGH.value).scalar() or 0
    critical = db.query(func.count(RiskAssessment.id)).filter(RiskAssessment.level == RiskLevel.CRITICAL.value).scalar() or 0

    approval_rate = (approved / total_apps * 100) if total_apps else 0
    rejection_rate = (rejected / total_apps * 100) if total_apps else 0
    human_review_rate = (in_review / total_apps * 100) if total_apps else 0

    apps_over_time = []
    for i in range(30):
        day = (now - timedelta(days=29 - i)).date()
        count = db.query(func.count(Application.id)).filter(
            func.date(Application.created_at) == day
        ).scalar() or 0
        apps_over_time.append({"date": day.isoformat(), "value": count})

    risk_dist = []
    for level in ["low", "medium", "high", "critical"]:
        count = db.query(func.count(RiskAssessment.id)).filter(RiskAssessment.level == level).scalar() or 0
        risk_dist.append({"label": level, "value": count})

    status_dist = []
    for status in ["draft", "submitted", "processing", "in_review", "approved", "rejected", "needs_resubmission", "escalated"]:
        count = db.query(func.count(Application.id)).filter(Application.status == status).scalar() or 0
        status_dist.append({"label": status, "value": count})

    doc_types = []
    for dt in ["passport", "national_id", "driver_license", "proof_of_address", "selfie", "business", "residence"]:
        count = db.query(func.count(Document.id)).filter(Document.doc_type == dt).scalar() or 0
        doc_types.append({"label": dt, "value": count})

    funnel_steps = [
        ("درخواست", total_apps),
        ("مدارک", db.query(func.count(Document.id)).scalar() or 0),
        ("OCR", db.query(func.count(Verification.id)).filter(Verification.kind == "ocr").scalar() or 0),
        ("چهره", db.query(func.count(Verification.id)).filter(Verification.kind == "face").scalar() or 0),
        ("ریسک", db.query(func.count(RiskAssessment.id)).scalar() or 0),
        ("بررسی", in_review),
        ("تأیید", approved),
    ]
    verification_funnel = [
        {"step": step, "count": count, "percentage": (count / total_apps * 100) if total_apps else 0}
        for step, count in funnel_steps
    ]

    return {
        "kpis": {
            "total_applications": total_apps,
            "new_applications": new_apps,
            "approved_count": approved,
            "rejected_count": rejected,
            "in_review_count": in_review,
            "approval_rate": round(approval_rate, 1),
            "rejection_rate": round(rejection_rate, 1),
            "human_review_rate": round(human_review_rate, 1),
            "avg_processing_hours": 0,
            "avg_review_hours": 0,
            "high_risk_count": high_risk,
            "critical_count": critical,
            "total_customers": total_customers,
            "total_cases": total_cases,
            "open_cases": open_cases,
        },
        "applications_over_time": apps_over_time,
        "risk_distribution": risk_dist,
        "verification_funnel": verification_funnel,
        "document_type_distribution": doc_types,
        "status_distribution": status_dist,
    }


@router.get("/reviewer-workload")
def reviewer_workload(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    reviewers = db.query(User).filter(User.role.in_(["reviewer", "analyst"])).all()
    result = []
    for r in reviewers:
        count = db.query(func.count(Case.id)).filter(Case.assigned_to == r.id, Case.status.in_(["open", "assigned", "in_review"])).scalar() or 0
        result.append({"label": r.full_name, "value": count})
    return result
