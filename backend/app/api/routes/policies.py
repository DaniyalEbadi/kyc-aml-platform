from __future__ import annotations

import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.errors import not_found
from app.db.session import get_db
from app.domain.enums import RoleName
from app.models.entities import Policy, PolicyVersion, PolicyChunk, User
from app.schemas.policy import PolicyCreate, PolicySearchRequest
from app.rag.retriever import PolicyRetriever

router = APIRouter()


@router.get("")
def list_policies(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    policies = db.query(Policy).all()
    result = []
    for p in policies:
        versions = db.query(PolicyVersion).filter(PolicyVersion.policy_id == p.id).all()
        result.append({
            "id": p.id,
            "code": p.code,
            "title": p.title,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "versions": [
                {
                    "id": v.id,
                    "version": v.version,
                    "is_active": v.is_active,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "chunk_count": db.query(PolicyChunk).filter(PolicyChunk.version_id == v.id).count(),
                }
                for v in versions
            ],
        })
    return result


@router.get("/{policy_id}")
def get_policy(policy_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    policy = db.get(Policy, policy_id)
    if not policy:
        raise not_found("سیاست")
    versions = db.query(PolicyVersion).filter(PolicyVersion.policy_id == policy.id).all()
    return {
        "id": policy.id,
        "code": policy.code,
        "title": policy.title,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "is_active": v.is_active,
                "body": v.body,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "chunks": [
                    {"id": c.id, "clause": c.clause, "section": c.section, "text": c.text}
                    for c in db.query(PolicyChunk).filter(PolicyChunk.version_id == v.id).all()
                ],
            }
            for v in versions
        ],
    }


@router.post("")
def create_policy(body: PolicyCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(RoleName.ADMIN))):
    policy = Policy(code=body.code, title=body.title)
    db.add(policy)
    db.flush()
    version = PolicyVersion(policy_id=policy.id, version=body.version, body=body.body)
    db.add(version)
    db.flush()
    sections = re.split(r"\n##\s+", body.body)
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n", 1)
        section_title = lines[0].strip() if lines else f"بخش {i+1}"
        section_text = lines[1].strip() if len(lines) > 1 else section
        clauses = re.findall(r"(\d+\.\d+)\s", section_text)
        if clauses:
            for clause in clauses:
                db.add(PolicyChunk(version_id=version.id, clause=clause, section=section_title, text=section_text[:500]))
        else:
            db.add(PolicyChunk(version_id=version.id, clause=f"{i+1}.0", section=section_title, text=section_text[:500]))
    db.commit()
    return {"id": policy.id, "code": policy.code}


@router.post("/search")
def search_policies(body: PolicySearchRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    retriever = PolicyRetriever()
    return retriever.retrieve(db, body.query, body.top_k)
