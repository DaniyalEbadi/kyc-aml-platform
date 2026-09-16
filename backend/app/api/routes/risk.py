from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User, RiskAssessment, RiskFactor

router = APIRouter()


@router.get("/{application_id}")
def get_risk_assessment(application_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    risk = db.query(RiskAssessment).filter(RiskAssessment.application_id == application_id).order_by(RiskAssessment.created_at.desc()).first()
    if not risk:
        return None
    factors = db.query(RiskFactor).filter(RiskFactor.assessment_id == risk.id).all()
    return {
        "id": risk.id,
        "application_id": risk.application_id,
        "score": risk.score,
        "level": risk.level,
        "recommended_decision": risk.recommended_decision,
        "explanation": risk.explanation,
        "created_at": risk.created_at.isoformat() if risk.created_at else None,
        "factors": [
            {
                "id": f.id,
                "code": f.code,
                "label": f.label,
                "weight": f.weight,
                "triggered": f.triggered,
                "detail": f.detail,
            }
            for f in factors
        ],
    }
