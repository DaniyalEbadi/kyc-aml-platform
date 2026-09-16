from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class APIError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "details": details or {}})
        self.code = code
        self.message = message
        self.details = details or {}


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = {}


async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "details": exc.details},
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "خطای داخلی سامانه. لطفاً دوباره تلاش کنید.",
            "details": {},
        },
    )


def not_found(entity: str = "مورد") -> APIError:
    return APIError(404, "not_found", f"{entity} یافت نشد.")


def forbidden() -> APIError:
    return APIError(403, "forbidden", "شما اجازه دسترسی به این بخش را ندارید.")


def unauthorized(message: str = "احراز هویت لازم است.") -> APIError:
    return APIError(401, "unauthorized", message)


def bad_request(message: str, details: dict | None = None) -> APIError:
    return APIError(400, "bad_request", message, details)
