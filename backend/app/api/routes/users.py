from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.errors import not_found
from app.db.session import get_db
from app.domain.enums import RoleName
from app.models.entities import User

router = APIRouter()


@router.get("")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles(RoleName.ADMIN))):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(require_roles(RoleName.ADMIN))):
    user = db.get(User, user_id)
    if not user:
        raise not_found("کاربر")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
