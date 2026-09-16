from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.errors import bad_request, not_found
from app.db.session import get_db
from app.domain.enums import CaseStatus, RoleName
from app.models.entities import Case, CaseAssignment, Customer, Application, Review, User
from app.schemas.case import CaseAssignRequest, CaseReviewRequest, CaseUpdateRequest

router = APIRouter()


@router.get("")
def list_cases(
    status: str | None = None,
    priority: str | None = None,
    risk_level: str | None = None,
    assigned_to: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Case)
    if status:
        q = q.filter(Case.status == status)
    if priority:
        q = q.filter(Case.priority == priority)
    if risk_level:
        q = q.filter(Case.risk_level == risk_level)
    if assigned_to:
        q = q.filter(Case.assigned_to == assigned_to)
    if search:
        q = q.join(Application).join(Customer).filter(
            or_(
                Case.case_number.ilike(f"%{search}%"),
                Application.application_number.ilike(f"%{search}%"),
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
            )
        )

    total = q.count()
    items = q.order_by(Case.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for case in items:
        app = db.get(Application, case.application_id)
        customer = db.get(Customer, case.customer_id)
        result.append({
            "id": case.id,
            "case_number": case.case_number,
            "application_id": case.application_id,
            "customer_id": case.customer_id,
            "status": case.status,
            "priority": case.priority,
            "risk_level": case.risk_level,
            "assigned_to": case.assigned_to,
            "sla_hours": case.sla_hours,
            "sla_due_at": case.sla_due_at.isoformat() if case.sla_due_at else None,
            "decision": case.decision,
            "decision_reason": case.decision_reason,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "customer_name": f"{customer.first_name} {customer.last_name}" if customer else "",
            "application_number": app.application_number if app else "",
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = db.get(Case, case_id)
    if not case:
        raise not_found("پرونده")
    app = db.get(Application, case.application_id)
    customer = db.get(Customer, case.customer_id)
    reviews = db.query(Review).filter(Review.case_id == case.id).order_by(Review.created_at.desc()).all()
    assignments = db.query(CaseAssignment).filter(CaseAssignment.case_id == case.id).all()
    return {
        "id": case.id,
        "case_number": case.case_number,
        "application_id": case.application_id,
        "customer_id": case.customer_id,
        "status": case.status,
        "priority": case.priority,
        "risk_level": case.risk_level,
        "assigned_to": case.assigned_to,
        "sla_hours": case.sla_hours,
        "sla_due_at": case.sla_due_at.isoformat() if case.sla_due_at else None,
        "decision": case.decision,
        "decision_reason": case.decision_reason,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "customer_name": f"{customer.first_name} {customer.last_name}" if customer else "",
        "application_number": app.application_number if app else "",
        "reviews": [
            {"id": r.id, "reviewer_id": r.reviewer_id, "action": r.action, "reason": r.reason, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in reviews
        ],
        "assignments": [
            {"id": a.id, "user_id": a.user_id, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in assignments
        ],
    }


@router.post("/{case_id}/assign")
def assign_case(case_id: str, body: CaseAssignRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.REVIEWER, RoleName.ADMIN, RoleName.ANALYST))):
    case = db.get(Case, case_id)
    if not case:
        raise not_found("پرونده")
    case.assigned_to = body.user_id
    case.status = CaseStatus.ASSIGNED.value
    db.add(CaseAssignment(case_id=case.id, user_id=body.user_id))
    db.commit()
    return {"message": "پرونده با موفقیت اختصاص داده شد."}


@router.post("/{case_id}/review")
def review_case(case_id: str, body: CaseReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.REVIEWER, RoleName.ADMIN, RoleName.ANALYST))):
    case = db.get(Case, case_id)
    if not case:
        raise not_found("پرونده")
    if body.action not in ("approve", "reject", "resubmit", "escalate"):
        raise bad_request("عملیات نامعتبر است.")
    from app.domain.enums import ApplicationStatus, DecisionCode
    from app.models.entities import Application, Decision
    app = db.get(Application, case.application_id)
    case.decision = body.action
    case.decision_reason = body.reason
    case.status = CaseStatus.CLOSED.value
    db.add(Review(case_id=case.id, reviewer_id=user.id, action=body.action, reason=body.reason))
    if body.action == "approve":
        app.status = ApplicationStatus.APPROVED.value
        from datetime import datetime, timezone
        app.decided_at = datetime.now(timezone.utc)
        db.add(Decision(application_id=app.id, code=DecisionCode.APPROVED.value, source="human_reviewer", reason=body.reason, actor_id=user.id))
    elif body.action == "reject":
        app.status = ApplicationStatus.REJECTED.value
        from datetime import datetime, timezone
        app.decided_at = datetime.now(timezone.utc)
        db.add(Decision(application_id=app.id, code=DecisionCode.REJECTED.value, source="human_reviewer", reason=body.reason, actor_id=user.id))
    elif body.action == "resubmit":
        app.status = ApplicationStatus.NEEDS_RESUBMISSION.value
    elif body.action == "escalate":
        app.status = ApplicationStatus.ESCALATED.value
    db.commit()
    return {"message": "بررسی با موفقیت ثبت شد."}


@router.put("/{case_id}")
def update_case(case_id: str, body: CaseUpdateRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.REVIEWER, RoleName.ADMIN))):
    case = db.get(Case, case_id)
    if not case:
        raise not_found("پرونده")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    db.commit()
    return {"message": "پرونده به‌روزرسانی شد."}
