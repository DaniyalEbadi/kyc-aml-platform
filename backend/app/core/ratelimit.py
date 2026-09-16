from __future__ import annotations

from collections import defaultdict, deque
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)
        key = request.client.host if request.client else "anon"
        now = time()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"code": "rate_limited", "message": "تعداد درخواست‌ها بیش از حد مجاز است.", "details": {}},
            )
        window.append(now)
        return await call_next(request)
