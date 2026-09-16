from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User, ScreeningResult

router = APIRouter()


@router.get("/{application_id}")
def get_screening_results(application_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results = db.query(ScreeningResult).filter(ScreeningResult.application_id == application_id).order_by(ScreeningResult.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "kind": s.kind,
            "matched": s.matched,
            "score": s.score,
            "list_name": s.list_name,
            "matched_name": s.matched_name,
            "is_simulated": s.is_simulated,
            "payload": s.payload,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in results
    ]
