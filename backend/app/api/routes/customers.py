from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.core.errors import not_found
from app.db.session import get_db
from app.domain.enums import RoleName
from app.models.entities import Application, Customer, CustomerNote, User
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut, CustomerNoteCreate, CustomerNoteOut

router = APIRouter()


@router.get("")
def list_customers(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleName.ANALYST, RoleName.REVIEWER, RoleName.ADMIN, RoleName.AUDITOR)),
):
    q = db.query(Customer)
    if search:
        q = q.filter(
            or_(
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
                Customer.national_id.ilike(f"%{search}%"),
                Customer.passport_number.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%"),
            )
        )
    total = q.count()
    items = q.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                **{k: v for k, v in c.__dict__.items() if not k.startswith("_")},
                "application_count": db.query(func.count(Application.id)).filter(Application.customer_id == c.id).scalar() or 0,
            }
            for c in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=CustomerOut)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ANALYST, RoleName.REVIEWER, RoleName.ADMIN))):
    customer = Customer(**body.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return CustomerOut.model_validate(customer)


@router.get("/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = db.query(Customer).options(joinedload(Customer.applications)).filter(Customer.id == customer_id).first()
    if not customer:
        raise not_found("مشتری")
    from app.domain.enums import RoleName
    if user.role == RoleName.APPLICANT.value and customer.user_id != user.id:
        from app.core.errors import forbidden
        raise forbidden()
    apps = db.query(Application).filter(Application.customer_id == customer_id).order_by(Application.created_at.desc()).all()
    notes = db.query(CustomerNote).filter(CustomerNote.customer_id == customer_id).order_by(CustomerNote.created_at.desc()).all()
    return {
        **{k: v for k, v in customer.__dict__.items() if not k.startswith("_")},
        "applications": [
            {
                "id": a.id,
                "application_number": a.application_number,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in apps
        ],
        "notes": [
            {
                "id": n.id,
                "body": n.body,
                "author_id": n.author_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
        "application_count": len(apps),
    }


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: str, body: CustomerUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles(RoleName.ANALYST, RoleName.REVIEWER, RoleName.ADMIN))):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise not_found("مشتری")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return CustomerOut.model_validate(customer)


@router.post("/{customer_id}/notes", response_model=CustomerNoteOut)
def add_customer_note(customer_id: str, body: CustomerNoteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise not_found("مشتری")
    note = CustomerNote(customer_id=customer_id, author_id=user.id, body=body.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return CustomerNoteOut.model_validate(note)
