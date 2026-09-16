from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import forbidden, unauthorized
from app.core.security import decode_token
from app.db.session import get_db
from app.domain.enums import RoleName
from app.models.entities import User

bearer = HTTPBearer(auto_error=False)

STAFF = {RoleName.ANALYST, RoleName.REVIEWER, RoleName.ADMIN, RoleName.AUDITOR}
REVIEW_ROLES = {RoleName.REVIEWER, RoleName.ADMIN, RoleName.ANALYST}


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise unauthorized()
    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise unauthorized("توکن نامعتبر یا منقضی است.")
    if payload.get("typ") != "access":
        raise unauthorized("نوع توکن نادرست است.")
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise unauthorized()
    return user


def require_roles(*roles: RoleName):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in {r.value for r in roles} and user.role != RoleName.ADMIN.value:
            raise forbidden()
        return user

    return dep


def client_meta(request: Request) -> dict:
    return {"ip": request.client.host if request.client else None, "ua": request.headers.get("user-agent")}
