from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User, FaceVerification
from app.services.kyc import compare_faces
from app.schemas.verification import VerificationOut

router = APIRouter()


@router.post("/face")
async def face_compare(
    app_id: str = Form(...),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    selfie_bytes = await selfie.read()
    result = compare_faces(db, user, app_id, selfie_bytes, None)
    return {
        "id": result.id,
        "similarity": result.similarity,
        "quality_score": result.quality_score,
        "confidence": result.confidence,
        "decision": result.decision,
        "reasons": result.reasons,
        "is_simulated": result.is_simulated,
    }


@router.get("/face/{application_id}")
def get_face_verification(application_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    face = db.query(FaceVerification).filter(FaceVerification.application_id == application_id).order_by(FaceVerification.created_at.desc()).first()
    if not face:
        return None
    return {
        "id": face.id,
        "application_id": face.application_id,
        "similarity": face.similarity,
        "quality_score": face.quality_score,
        "confidence": face.confidence,
        "decision": face.decision,
        "reasons": face.reasons,
        "is_simulated": face.is_simulated,
        "created_at": face.created_at.isoformat() if face.created_at else None,
    }


@router.get("/{application_id}")
def get_verifications(application_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.entities import Verification
    vers = db.query(Verification).filter(Verification.application_id == application_id).order_by(Verification.created_at.desc()).all()
    return [
        {
            "id": v.id,
            "kind": v.kind,
            "status": v.status,
            "score": v.score,
            "details": v.details,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in vers
    ]
