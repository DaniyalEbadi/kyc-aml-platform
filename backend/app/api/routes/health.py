from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "demo_mode": settings.demo_mode,
    }
