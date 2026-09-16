from __future__ import annotations

from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    type: str
    title: str
    subtitle: str = ""
    url: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResult] = []
    total: int = 0
