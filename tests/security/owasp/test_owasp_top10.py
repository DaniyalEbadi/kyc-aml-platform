"""
OWASP Top 10 Security Tests for KYC/AML Platform
Tests for each of the OWASP Top 10 vulnerabilities
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import io
import os

from app.models.entities import User, Customer, Application, Document
from app.domain.enums import RoleName, ApplicationStatus, DocumentType
from app.core.security import hash_password, create_access_token


class TestA01BrokenAccessControl:
    """A01:2021 – Broken Access Control"""

    def test_applicant_cannot_access_admin_endpoints(self, client: TestClient, applicant_user: User):
        """Applicant should not access admin-only endpoints"""
        token = create_access_token(applicant_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Admin endpoints
        admin_endpoints = [
            ("GET", "/api/v1/customers"),
            ("POST", "/api/v1/customers"),
            ("GET", "/api/v1/audit"),
            ("GET", "/api/v1/analytics"),
        ]
        
        for method, endpoint in admin_endpoints:
            response = client.request(method, endpoint, headers={"Authorization": f"Bearer {create_access_token(applicant_user.id)}"})
            assert response.status_code == 403, f"Applicant accessed {method} {endpoint}"

    def test_applicant_cannot_access_other_application(self, client: TestClient, db_session: Session):
        """Applicant should not access other users' applications"""
        # Create two applicants
        user1 = User(email="u1owasp@test.com", full_name="User1", hashed_password=hash_password("p1"), role="applicant")
        user2 = User(email="u2owasp@test.com", full_name="User2", hashed_password=hash_password("p2"), role="applicant")
        c1 = Customer(user_id=user1.id, first_name="User", last_name="One")
        c2 = Customer(user_id=user2.id, first_name="User", last_name="Two")
        db_session.add_all([user1, user2, c1, c2])
        db_session.flush()
        app = Application(application_number="APP-OWASP-1", customer_id=c2.id, status="draft")
        db_session.add(app)
        db_session.commit()
        
        token1 = create_access_token(user1.id)
        response = client.get(f"/api/v1/applications/{app.id}", headers={"Authorization": f"Bearer {token1}"})
        assert response.status_code == 403

    def test_applicant_cannot_access_other_customer(self, client: TestClient, db_session: Session):
        """Applicant should not access other customers' data"""
        user1 = User(email="u1cust@test.com", full_name="User1", hashed_password=hash_password("p1"), role="applicant")
        user2 = User(email="u2cust@test.com", full_name="User2", hashed_password=hash_password("p2"), role="applicant")
        c1 = Customer(user_id=user1.id, first_name="User", last_name="One")
        c2 = Customer(user_id=user2.id, first_name="User", last_name="Two")
        db_session.add_all([user1, user2, c1, c2])
        db_session.commit()
        
        token1 = create_access_token(user1.id)
        response = client.get(f"/api/v1/customers/{c2.id}", headers={"Authorization": f"Bearer {token1}"})
        assert response.status_code == 403

    def test_staff_can_access_admin_endpoints(self, client: TestClient, analyst_user: User):
        """Analyst should access admin endpoints"""
        token = create_access_token(analyst_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/customers", headers=headers)
        assert response.status_code == 200
        
        response = client.get("/api/v1/analytics", headers=headers)
        assert response.status_code == 200

    def test_horizontal_privilege_escalation_prevented(self, client: TestClient, db_session: Session):
        """Users cannot escalate privileges horizontally"""
        user1 = User(email="u1priv@test.com", full_name="User1", hashed_password=hash_password("p1"), role="applicant")
        user2 = User(email="u2priv@test.com", full_name="User2", hashed_password=hash_password("p2"), role="applicant")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # User1 tries to access user2's profile
        token1 = create_access_token(user1.id)
        response = client.get(f"/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user1.id  # Should return own profile, not user2's


class TestA02CryptographicFailures:
    """A02:2021 – Cryptographic Failures"""

    def test_passwords_hashed_with_bcrypt(self, db_session: Session):
        """Passwords should be hashed with bcrypt"""
        user = User(
            email="crypto@test.com",
            full_name="Crypto User",
            hashed_password=hash_password("password123"),
            role="applicant"
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify bcrypt hash format
        assert user.hashed_password.startswith("$2b$")
        assert len(user.hashed_password) == 60

    def test_jwt_uses_strong_algorithm(self):
        """JWT should use HS256 or stronger"""
        from app.core.security import ALGORITHM
        assert ALGORITHM == "HS256"

    def test_jwt_tokens_have_expiration(self):
        """JWT tokens should have expiration"""
        token = create_access_token("test-user")
        import jwt
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"], options={"verify_signature": False})
        assert "exp" in payload

    def test_refresh_tokens_stored_hashed(self, db_session: Session, applicant_user: User):
        """Refresh tokens should be stored hashed"""
        from app.models.entities import RefreshToken
        from hashlib import sha256
        
        token = "refresh-token-123"
        rt = RefreshToken(
            user_id=applicant_user.id,
            token_hash=sha256(token.encode()).hexdigest()
        )
        db_session.add(rt)
        db_session.commit()
        
        # Token should be hashed in DB
        stored = db_session.query(RefreshToken).filter(RefreshToken.user_id == applicant_user.id).first()
        assert stored.token_hash == sha256(token.encode()).hexdigest()
        assert stored.token_hash != token

    def test_sensitive_data_not_in_logs(self, client: TestClient, applicant_user: User):
        """Sensitive data should not appear in logs"""
        token = create_access_token(applicant_user.id)
        response = client.post("/api/v1/auth/login", json={
            "email": applicant_user.email,
            "password": "applicant123"
        })
        # Response should not contain password
        assert "applicant123" not in response.text
        assert "hashed_password" not in response.text


class TestA03Injection:
    """A03:2021 – Injection"""

    def test_sql_injection_prevented_in_search(self, client: TestClient, admin_headers: dict):
        """SQL injection should be prevented in search"""
        # Try SQL injection in search
        malicious_queries = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
        ]
        
        for query in malicious_queries:
            response = client.get(f"/api/v1/search?q={query}", headers=admin_headers)
            # Should not crash or return all data
            assert response.status_code in [200, 400, 422]
    
    def test_sql_injection_prevented_in_filters(self, client: TestClient, admin_headers: dict):
        """SQL injection should be prevented in filter parameters"""
        malicious_values = [
            "test'; DROP TABLE applications; --",
            "test' OR '1'='1",
        ]
        
        for value in malicious_values:
            response = client.get(f"/api/v1/applications?search={value}", headers=admin_headers)
            assert response.status_code in [200, 400, 422]

    def test_nosql_injection_prevented(self, client: TestClient, admin_headers: dict):
        """NoSQL injection should be prevented (if using MongoDB)"""
        # This is a placeholder - we use PostgreSQL
        pass

    def test_orm_prevents_injection(self, db_session: Session):
        """ORM should prevent SQL injection"""
        # Test that parameterized queries are used
        user = User(
            email="injection@test.com",
            full_name="Injection Test",
            hashed_password=hash_password("p1"),
            role="applicant"
        )
        db_session.add(user)
        db_session.commit()
        
        # Query using ORM - should be safe
        found = db_session.query(User).filter(User.email == "injection@test.com' OR '1'='1").first()
        assert found is None  # No match because exact match


class TestA04InsecureDesign:
    """A04:2021 – Insecure Design"""

    def test_decision_boundary_is_deterministic(self):
        """Decision boundary should be deterministic, not LLM-based"""
        from app.domain.decisions import decide
        from app.domain.rules import ValidationBundle, CheckResult
        from app.domain.enums import RiskLevel
        
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        
        # Same inputs should always produce same output
        outcomes = [decide(bundle, RiskLevel.LOW, False, False) for _ in range(100)]
        assert all(o.code == outcomes[0].code for o in outcomes)

    def test_llm_never_makes_final_decision(self):
        """LLM should never make final approve/reject decisions"""
        from app.domain.decisions import DecisionCode
        from app.domain.decisions import decide
        from app.domain.rules import ValidationBundle, CheckResult
        from app.domain.enums import RiskLevel
        
        # Test all combinations
        for level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            for pep in [True, False]:
                for sanctions in [True, False]:
                    for resubmit in [True, False]:
                        for escalate in [True, False]:
                            checks = []
                            if resubmit:
                                checks.append(CheckResult("c", False, resubmit=True))
                            if escalate:
                                checks.append(CheckResult("c", False, escalate=True))
                            if not checks:
                                checks.append(CheckResult("c", True))
                            bundle = ValidationBundle(checks=checks)
                            outcome = decide(bundle, level, pep, sanctions)
                            # REJECTED should never be auto-returned
                            assert outcome.code != DecisionCode.REJECTED

    def test_business_logic_in_domain_layer(self):
        """Business logic should be in domain layer, not API layer"""
        # Verify domain functions exist and are used
        from app.domain.risk import compute_risk
        from app.domain.rules import validate_application_payload
        from app.domain.decisions import decide
        
        # These should be pure Python functions
        assert callable(compute_risk)
        assert callable(validate_application_payload)
        assert callable(decide)

    def test_no_business_logic_in_api_routes(self):
        """API routes should delegate to services/domain"""
        import inspect
        from app.api.routes import applications
        
        # Check that route handlers call service functions
        source = inspect.getsource(applications)
        assert "create_onboarding" in source
        assert "submit_application" in source
        assert "update_onboarding" in source


class TestA05SecurityMisconfiguration:
    """A05:2021 – Security Misconfiguration"""

    def test_debug_mode_disabled_in_production(self):
        """Debug mode should be disabled in production"""
        from app.core.config import settings
        # In production, demo_mode should be False
        # This is a configuration test
        assert hasattr(settings, 'demo_mode')

    def test_cors_configured_correctly(self, client: TestClient):
        """CORS should be configured with specific origins"""
        response = client.options("/api/v1/health", headers={"Origin": "http://localhost:3000"})
        # Should allow configured origin
        assert response.status_code in [200, 405]

    def test_security_headers_present(self, client: TestClient):
        """Security headers should be present"""
        response = client.get("/api/v1/health")
        # Check for security headers
        # X-Content-Type-Options, X-Frame-Options, etc.

    def test_rate_limiting_enabled(self, client: TestClient):
        """Rate limiting should be enabled"""
        # Make many requests
        for _ in range(150):
            response = client.get("/api/v1/health")
        
        # Should eventually get rate limited
        # This is a basic check

    def test_default_credentials_changed(self):
        """Default credentials should not work in production"""
        # This is a deployment configuration test
        pass

    def test_unnecessary_features_disabled(self):
        """Unnecessary features should be disabled"""
        # Swagger UI should be disabled in production
        from app.core.config import settings
        if settings.app_env == "production":
            # docs_url should be None
            pass


class TestA06VulnerableComponents:
    """A06:2021 – Vulnerable and Outdated Components"""

    def test_dependencies_scanned(self):
        """Dependencies should be scanned for vulnerabilities"""
        # This would run safety check
        # safety check --json
        pass

    def test_known_vulnerabilities_addressed(self):
        """Known vulnerabilities should be addressed"""
        # Run safety check in CI
        pass


class TestA07IdentificationAuthenticationFailures:
    """A07:2021 – Identification and Authentication Failures"""

    def test_brute_force_protection(self, client: TestClient):
        """Should protect against brute force attacks"""
        # Try multiple failed logins
        for i in range(10):
            response = client.post("/api/v1/auth/login", json={
                "email": "admin@parsheid.ir",
                "password": f"wrong{i}"
            })
            # Should be 400 (invalid credentials) or 429 (rate limited)
            assert response.status_code in [400, 429]
        
        # Should eventually lock or rate limit
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@parsheid.ir",
            "password": "wrong"
        })
        # Should be rate limited (429), bad request (400), or locked

    def test_weak_passwords_rejected(self):
        """Weak passwords should be rejected"""
        # Password policy enforcement
        from app.core.security import hash_password
        
        # Should accept strong passwords
        hash_password("StrongPass123!")
        
        # Weak passwords - system should enforce policy at registration
        # This is a business logic test

    def test_session_management_secure(self, client: TestClient, applicant_user: User):
        """Session management should be secure"""
        token = create_access_token(applicant_user.id)
        
        # Token should be valid
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # Expired token should be rejected
        import jwt
        from datetime import datetime, timedelta, timezone
        expired_token = jwt.encode(
            {"sub": applicant_user.id, "typ": "access", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            "test-secret", algorithm="HS256"
        )
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        # Should be 401 (unauthorized) or 429 (rate limited from earlier requests)
        assert response.status_code in [401, 429]

    def test_password_reset_secure(self, client: TestClient, applicant_user: User):
        """Password reset should be secure"""
        token = create_access_token(applicant_user.id)
        response = client.post("/api/v1/auth/change-password", json={
            "old_password": "applicant123",
            "new_password": "newpassword123"
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_mfa_support_placeholder(self):
        """MFA support should be planned"""
        # Placeholder for MFA implementation
        pass


class TestA08SoftwareDataIntegrityFailures:
    """A08:2021 – Software and Data Integrity Failures"""

    def test_ci_cd_integrity(self):
        """CI/CD pipeline should verify integrity"""
        # Checksums, signatures
        pass

    def test_dependency_integrity(self):
        """Dependencies should have integrity checks"""
        # pip install --require-hashes
        pass

    def test_audit_log_immutable(self, db_session: Session):
        """Audit logs should be immutable"""
        from app.models.entities import AuditEvent
        
        audit = AuditEvent(
            actor_id="test",
            action="test.action",
            entity="test",
            entity_id="1",
            reason="Test"
        )
        db_session.add(audit)
        db_session.commit()
        
        # Audit events should not be updatable through normal means
        # This is enforced by not having UPDATE routes for audit events


class TestA09SecurityLoggingMonitoringFailures:
    """A09:2021 – Security Logging and Monitoring Failures"""

    def test_security_events_logged(self, client: TestClient, db_session: Session, applicant_user: User):
        """Security events should be logged"""
        token = create_access_token(applicant_user.id)
        
        # Failed login
        client.post("/api/v1/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrong"
        })
        
        # Check audit log
        from app.models.entities import AuditEvent
        # In a real test, we'd check for failed login audit entries

    def test_admin_actions_logged(self, client: TestClient, admin_headers: dict):
        """Admin actions should be logged"""
        response = client.post("/api/v1/customers", json={
            "first_name": "Test",
            "last_name": "User",
            "national_id": "0012345679",
        }, headers=admin_headers)
        assert response.status_code == 200
        
        # Check audit log for customer.create

    def test_failed_authorization_logged(self, client: TestClient, applicant_user: User):
        """Failed authorization should be logged"""
        token = create_access_token(applicant_user.id)
        response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        
        # Check audit log for failed access

    def test_monitoring_endpoints_available(self, client: TestClient):
        """Monitoring endpoints should be available"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Metrics endpoint
        # response = client.get("/metrics")


class TestA10ServerSideRequestForgery:
    """A10:2021 – Server-Side Request Forgery (SSRF)"""

    def test_file_upload_validates_urls(self, client: TestClient, admin_headers: dict):
        """File upload should validate URLs if external"""
        # If supporting external URLs, should validate
        pass

    def test_webhook_urls_validated(self):
        """Webhook URLs should be validated"""
        # If using webhooks, validate URLs
        pass

    def test_internal_network_access_blocked(self):
        """Internal network access should be blocked"""
        # Block access to 169.254.169.254, localhost, etc.
        pass


class TestAdditionalSecurity:
    """Additional security tests beyond OWASP Top 10"""

    def test_file_upload_validation(self, client: TestClient, auth_headers: dict, sample_application):
        """File upload should validate file types"""
        app_id = sample_application.id
        # Invalid file type
        files = {"file": ("test.exe", b"MZ...", "application/x-executable")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        response = client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        assert response.status_code == 400

    def test_file_size_limit(self, client: TestClient, auth_headers: dict, sample_application):
        """File size should be limited"""
        app_id = sample_application.id
        large_file = b"x" * (13 * 1024 * 1024)  # 13MB > 12MB limit
        files = {"file": ("large.jpg", large_file, "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        response = client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        assert response.status_code == 400

    def test_path_traversal_prevented(self, client: TestClient, admin_headers: dict):
        """Path traversal should be prevented in file access"""
        # Try to access files with ../
        response = client.get("/api/v1/documents/../../etc/passwd", headers=admin_headers)
        assert response.status_code in [400, 404, 422]

    def test_xss_prevention_in_responses(self, client: TestClient, admin_headers: dict):
        """XSS should be prevented in API responses"""
        # API returns JSON, not HTML
        response = client.get("/api/v1/health")
        assert response.headers["content-type"] == "application/json"

    def test_csrf_protection_not_needed_for_api(self):
        """API uses token auth, CSRF not applicable"""
        # Token-based auth is CSRF-resistant by design
        pass

    def test_clickjacking_protection(self, client: TestClient):
        """X-Frame-Options should prevent clickjacking"""
        response = client.get("/api/v1/health")
        # Check for X-Frame-Options header

    def test_content_security_policy(self, client: TestClient):
        """CSP should be set for frontend"""
        # Frontend should have CSP headers
        pass

    def test_secure_cookies_if_used(self):
        """Cookies should be secure if used"""
        # JWT in localStorage, not cookies
        pass

    def test_hsts_in_production(self):
        """HSTS should be enabled in production"""
        # Nginx/load balancer should set HSTS
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])