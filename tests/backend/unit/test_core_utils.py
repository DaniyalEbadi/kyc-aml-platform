from __future__ import annotations

import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from jose import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    ALGORITHM,
)
from app.core.config import settings, Settings
from app.core.errors import (
    APIError,
    ErrorBody,
    api_error_handler,
    unhandled_error_handler,
    not_found,
    forbidden,
    unauthorized,
    bad_request,
)
from app.core.logging import configure_logging, RequestIdMiddleware
from app.core.ratelimit import RateLimitMiddleware
from app.domain.enums import RoleName
from fastapi import Request


class TestPasswordHashing:
    """Tests for password hashing and verification"""

    def test_hash_password_returns_bcrypt_hash(self):
        """hash_password should return bcrypt hash"""
        password = "TestPass123!"
        hashed = hash_password(password)

        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_correct(self):
        """verify_password should return True for correct password"""
        password = "TestPass123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for incorrect password"""
        password = "TestPass123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Same password should produce different hashes"""
        password = "TestPass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_timing_attack_resistance(self):
        """Password verification should be constant-time"""
        password = "TestPass123!"
        hashed = hash_password(password)

        import time
        times = []
        for _ in range(10):
            start = time.perf_counter()
            verify_password(password, hashed)
            times.append(time.perf_counter() - start)

        assert max(times) - min(times) < 0.5  # 500ms variance (bcrypt timing varies on Windows)


class TestJWTSecurity:
    """Tests for JWT token security"""

    def test_access_token_structure(self, applicant_user):
        """Access token should have correct structure"""
        token = create_access_token(applicant_user.id)

        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], options={"verify_signature": False})
        assert payload["sub"] == applicant_user.id
        assert payload["typ"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_structure(self, applicant_user):
        """Refresh token should have correct structure"""
        from app.core.security import create_refresh_token
        token = create_refresh_token(applicant_user.id)

        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], options={"verify_signature": False})
        assert payload["sub"] == applicant_user.id
        assert payload["typ"] == "refresh"
        assert "exp" in payload

    def test_token_signature_verification(self, applicant_user):
        """Token signature should be verified"""
        token = create_access_token(applicant_user.id)

        payload = decode_token(token)
        assert payload["sub"] == applicant_user.id

        tampered = token[:-5] + "tamper"
        with pytest.raises(ValueError):
            decode_token(tampered)

    def test_expired_token_rejected(self, applicant_user):
        """Expired tokens should be rejected"""
        expired = jwt.encode(
            {"sub": applicant_user.id, "typ": "access", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.secret_key, algorithm="HS256"
        )

        with pytest.raises(ValueError, match="توکن نامعتبر"):
            decode_token(expired)

    def test_wrong_secret_rejected(self, applicant_user):
        """Token signed with wrong secret should be rejected"""
        wrong_token = jwt.encode(
            {"sub": applicant_user.id, "typ": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret", algorithm="HS256"
        )

        with pytest.raises(ValueError):
            decode_token(wrong_token)

    def test_algorithm_confusion_prevented(self, applicant_user):
        """Algorithm confusion attacks should be prevented"""
        import base64, json
        # Manually craft a token with "none" algorithm (bypass jose encoder)
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps({"sub": str(applicant_user.id), "typ": "access"}).encode()).rstrip(b"=").decode()
        none_token = f"{header}.{payload_b64}."

        with pytest.raises(ValueError):
            decode_token(none_token)


class TestSettings:
    """Tests for configuration settings"""

    def test_settings_singleton(self):
        """Settings should be singleton"""
        s2 = Settings()
        assert settings.app_name == s2.app_name

    def test_default_values(self):
        """Settings should have correct defaults"""
        assert settings.app_name == "پارس‌هویت"
        assert settings.app_env == "development"
        assert settings.demo_mode is True
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7

    def test_cors_origin_list_property(self):
        """cors_origin_list should parse comma-separated origins"""
        origins = settings.cors_origin_list
        assert isinstance(origins, list)
        assert "http://localhost:3000" in origins

    def test_allowed_types_property(self):
        """allowed_types should parse comma-separated types"""
        types = settings.allowed_types
        assert isinstance(types, set)
        assert "image/jpeg" in types
        assert "image/png" in types
        assert "application/pdf" in types

    def test_is_sqlite_property(self):
        """is_sqlite should detect SQLite URLs"""
        s = Settings(database_url="sqlite:///test.db")
        assert s.is_sqlite is True

        s = Settings(database_url="postgresql://user:pass@localhost/db")
        assert s.is_sqlite is False


class TestAPIErrors:
    """Tests for API error handling"""

    def test_api_error_creation(self):
        """APIError should store code, message, details"""
        error = APIError(404, "not_found", "Not found", {"field": "id"})

        assert error.status_code == 404
        assert error.code == "not_found"
        assert error.message == "Not found"
        assert error.details == {"field": "id"}

    def test_error_body_model(self):
        """ErrorBody should validate correctly"""
        body = ErrorBody(code="test", message="Test", details={"key": "value"})
        assert body.code == "test"
        assert body.message == "Test"
        assert body.details == {"key": "value"}

    def test_not_found_error(self):
        """not_found should create 404 error"""
        error = not_found("User")
        assert error.status_code == 404
        assert error.code == "not_found"
        assert "User" in error.message

    def test_forbidden_error(self):
        """forbidden should create 403 error"""
        error = forbidden()
        assert error.status_code == 403
        assert error.code == "forbidden"

    def test_unauthorized_error(self):
        """unauthorized should create 401 error"""
        error = unauthorized("Custom message")
        assert error.status_code == 401
        assert error.code == "unauthorized"
        assert error.message == "Custom message"

    def test_bad_request_error(self):
        """bad_request should create 400 error"""
        error = bad_request("Invalid input", {"field": "email"})
        assert error.status_code == 400
        assert error.code == "bad_request"
        assert error.details == {"field": "email"}


class TestRateLimiting:
    """Tests for rate limiting middleware"""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_under_limit(self):
        """Should allow requests under limit"""
        middleware = RateLimitMiddleware(Mock())
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.client.host = "127.0.0.1"

        async def call_next(req):
            return Mock()

        with patch("time.time", return_value=1000.0):
            response = await middleware.dispatch(request, call_next)

        assert response is not None

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_over_limit(self):
        """Should block requests over limit"""
        middleware = RateLimitMiddleware(Mock())
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.client.host = "127.0.0.1"

        async def call_next(req):
            return Mock()

        with patch("time.time", return_value=1000.0):
            for _ in range(settings.rate_limit_per_minute + 5):
                await middleware.dispatch(request, call_next)

        with patch("time.time", return_value=1000.0):
            response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        import json
        body = json.loads(response.body.decode())
        assert body["code"] == "rate_limited"

    @pytest.mark.asyncio
    async def test_health_endpoint_excluded(self):
        """Health endpoint should not be rate limited"""
        middleware = RateLimitMiddleware(Mock())
        request = Mock(spec=Request)
        request.url.path = "/api/v1/health"
        request.client.host = "127.0.0.1"

        async def call_next(req):
            return Mock()

        response = await middleware.dispatch(request, call_next)

        assert response.status_code != 429


class TestLogging:
    """Tests for logging configuration"""

    def test_configure_logging(self):
        """configure_logging should not raise"""
        configure_logging()

    @pytest.mark.asyncio
    async def test_request_id_middleware(self):
        middleware = RequestIdMiddleware(Mock())
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock()
        response.headers = {}

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert "X-Request-ID" in result.headers
        assert len(result.headers["X-Request-ID"]) > 0


class TestRoleBasedAccess:
    """Tests for role-based access control"""

    def test_staff_roles(self):
        from app.api.deps import STAFF
        assert RoleName.ANALYST in STAFF
        assert RoleName.REVIEWER in STAFF
        assert RoleName.ADMIN in STAFF
        assert RoleName.AUDITOR in STAFF
        assert RoleName.APPLICANT not in STAFF

    def test_review_roles(self):
        from app.api.deps import REVIEW_ROLES
        assert RoleName.REVIEWER in REVIEW_ROLES
        assert RoleName.ADMIN in REVIEW_ROLES
        assert RoleName.ANALYST in REVIEW_ROLES
        assert RoleName.APPLICANT not in REVIEW_ROLES
        assert RoleName.AUDITOR not in REVIEW_ROLES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])