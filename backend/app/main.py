from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import APIError, api_error_handler, unhandled_error_handler
from app.core.logging import RequestIdMiddleware, configure_logging
from app.core.ratelimit import RateLimitMiddleware
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.demo_mode:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

from app.api.routes import (  # noqa: E402
    analytics,
    applications,
    auth,
    audit,
    cases,
    customers,
    documents,
    health,
    jobs,
    notifications,
    policies,
    risk,
    search,
    screening,
    verification,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["احراز هویت"])
app.include_router(health.router, prefix="/api/v1/health", tags=["سلامت"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["مشتریان"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["درخواست‌ها"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["مدارک"])
app.include_router(verification.router, prefix="/api/v1/verification", tags=["احراز هویت"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["ریسک"])
app.include_router(screening.router, prefix="/api/v1/screening", tags=["غربالگری"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["پرونده‌ها"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["سیاست‌ها"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["ممیزی"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["تحلیل‌ها"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["اعلانات"])
app.include_router(search.router, prefix="/api/v1/search", tags=["جستجو"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["کارها"])
