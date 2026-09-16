from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Customer, Application, Case, Document, User

router = APIRouter()


@router.get("")
def global_search(
    q: str = Query("", min_length=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not q or len(q) < 2:
        return {"results": [], "total": 0}

    results = []
    pattern = f"%{q}%"

    customers = db.query(Customer).filter(
        or_(Customer.first_name.ilike(pattern), Customer.last_name.ilike(pattern), Customer.national_id.ilike(pattern), Customer.passport_number.ilike(pattern), Customer.email.ilike(pattern))
    ).limit(10).all()
    for c in customers:
        results.append({
            "id": c.id,
            "type": "customer",
            "title": f"{c.first_name} {c.last_name}",
            "subtitle": c.national_id or c.passport_number or "",
            "url": f"/customers/{c.id}",
        })

    apps = db.query(Application).filter(Application.application_number.ilike(pattern)).limit(10).all()
    for a in apps:
        results.append({
            "id": a.id,
            "type": "application",
            "title": a.application_number,
            "subtitle": a.status,
            "url": f"/applications/{a.id}",
        })

    cases = db.query(Case).filter(Case.case_number.ilike(pattern)).limit(10).all()
    for c in cases:
        results.append({
            "id": c.id,
            "type": "case",
            "title": c.case_number,
            "subtitle": c.status,
            "url": f"/cases/{c.id}",
        })

    return {"results": results, "total": len(results)}
