from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.entities import PolicyChunk, PolicyVersion


class PolicyRetriever:
    def retrieve(self, db: Session, query: str, top_k: int = 4) -> list[dict]:
        version = db.query(PolicyVersion).filter(PolicyVersion.is_active.is_(True)).first()
        if not version:
            return []
        chunks = db.query(PolicyChunk).filter(PolicyChunk.version_id == version.id).all()
        tokens = set(re.findall(r"[\wآ-ی]+", query.lower()))
        scored: list[tuple[int, PolicyChunk]] = []
        for chunk in chunks:
            chunk_tokens = set(re.findall(r"[\wآ-ی]+", chunk.text.lower()))
            overlap = len(tokens & chunk_tokens)
            if overlap:
                scored.append((overlap, chunk))
        scored.sort(key=lambda p: p[0], reverse=True)
        picked = [c for _, c in scored[:top_k]] or chunks[:top_k]
        return [
            {
                "clause": c.clause,
                "section": c.section,
                "text": c.text,
                "policy_version": version.version,
                "policy_version_id": version.id,
            }
            for c in picked
        ]
