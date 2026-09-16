from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Notification, User

router = APIRouter()


@router.get("")
def list_notifications(
    read: bool | None = None,
    kind: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if read is not None:
        q = q.filter(Notification.read == read)
    if kind:
        q = q.filter(Notification.kind == kind)
    total = q.count()
    items = q.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    unread_count = db.query(func.count(Notification.id)).filter(Notification.user_id == user.id, Notification.read.is_(False)).scalar() or 0
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "kind": n.kind,
                "read": n.read,
                "payload": n.payload,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size,
    }


@router.post("/read")
def mark_read(body: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.schemas.notification import NotificationMarkRead
    data = NotificationMarkRead(**body)
    if data.mark_all:
        db.query(Notification).filter(Notification.user_id == user.id, Notification.read.is_(False)).update({"read": True})
    elif data.notification_ids:
        db.query(Notification).filter(Notification.id.in_(data.notification_ids), Notification.user_id == user.id).update({"read": True})
    db.commit()
    return {"message": "اعلانات به‌روزرسانی شدند."}
