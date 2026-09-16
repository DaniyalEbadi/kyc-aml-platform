from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import bad_request
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut, RefreshRequest, ChangePasswordRequest
from app.services.kyc import authenticate
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.entities import RefreshToken
from hashlib import sha256

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user, access, refresh = authenticate(db, body.email, body.password)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise bad_request("توکن نامعتبر است.")
    if payload.get("typ") != "refresh":
        raise bad_request("نوع توکن نادرست است.")
    token_hash = sha256(body.refresh_token.encode()).hexdigest()
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked.is_(False)).first()
    if not rt:
        raise bad_request("توکن بازیابی منقضی یا باطل شده است.")
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise bad_request("کاربر یافت نشد یا غیرفعال است.")
    rt.revoked = True
    from app.core.security import create_access_token as cat, create_refresh_token as crt
    new_access = cat(user.id)
    new_refresh = crt(user.id)
    db.add(RefreshToken(user_id=user.id, token_hash=sha256(new_refresh.encode()).hexdigest()))
    db.commit()
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.hashed_password):
        raise bad_request("گذرواژه فعلی نادرست است.")
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "گذرواژه با موفقیت تغییر کرد."}
