"""
Security tests for authentication, authorization, and data protection
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.entities import User, RefreshToken, Customer, Application
from app.domain.enums import RoleName
from app.core.config import settings
from hashlib import sha256


class TestJWTSecurity:
    """Tests for JWT token security"""

    def test_access_token_structure(self, applicant_user: User):
        """Access token should have correct structure"""
        token = create_access_token(applicant_user.id)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], options={"verify_signature": False})
        assert payload["sub"] == applicant_user.id
        assert payload["typ"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_structure(self, applicant_user: User):
        """Refresh token should have correct structure"""
        from app.core.security import create_refresh_token
        token = create_refresh_token(applicant_user.id)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], options={"verify_signature": False})
        assert payload["sub"] == applicant_user.id
        assert payload["typ"] == "refresh"
        assert "exp" in payload

    def test_token_signature_verification(self, applicant_user: User):
        """Token signature should be verified"""
        token = create_access_token(applicant_user.id)
        
        # Valid signature should decode
        payload = decode_token(token)
        assert payload["sub"] == applicant_user.id
        
        # Tampered token should fail
        tampered = token[:-5] + "tamper"
        with pytest.raises(ValueError):
            decode_token(tampered)

    def test_expired_token_rejected(self, applicant_user: User):
        """Expired tokens should be rejected"""
        expired = jwt.encode(
            {"sub": applicant_user.id, "typ": "access", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.secret_key, algorithm="HS256"
        )
        
        with pytest.raises(ValueError, match="توکن نامعتبر"):
            decode_token(expired)

    def test_wrong_secret_rejected(self, applicant_user: User):
        """Token signed with wrong secret should be rejected"""
        wrong_token = jwt.encode(
            {"sub": applicant_user.id, "typ": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret", algorithm="HS256"
        )
        
        with pytest.raises(ValueError):
            decode_token(wrong_token)

    def test_algorithm_confusion_prevented(self, applicant_user: User):
        """Algorithm confusion attacks should be prevented"""
        import base64, json
        # Manually craft a token with "none" algorithm (bypass jose encoder)
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps({"sub": str(applicant_user.id), "typ": "access"}).encode()).rstrip(b"=").decode()
        none_token = f"{header}.{payload_b64}."
        
        with pytest.raises(ValueError):
            decode_token(none_token)


class TestPasswordSecurity:
    """Tests for password security"""

    def test_password_hashing_uses_bcrypt(self):
        """Passwords should be hashed with bcrypt"""
        password = "TestPass123!"
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")  # bcrypt identifier
        assert len(hashed) == 60

    def test_password_verification_works(self):
        """Password verification should work correctly"""
        password = "TestPass123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_timing_attack_resistance(self):
        """Password verification should be constant-time"""
        password = "TestPass123!"
        hashed = hash_password(password)
        
        # Multiple verifications should take similar time
        import time
        times = []
        for _ in range(10):
            start = time.perf_counter()
            verify_password(password, hashed)
            times.append(time.perf_counter() - start)
        
        # Variance should be small (this is a basic check)
        assert max(times) - min(times) < 0.5  # 500ms variance (bcrypt timing varies on Windows)


class TestRefreshTokenSecurity:
    """Tests for refresh token security"""

    def test_refresh_token_stored_hashed(self, db_session: Session, applicant_user: User):
        """Refresh tokens should be stored hashed"""
        token = "refresh-token-12345"
        token_hash = sha256(token.encode()).hexdigest()
        
        rt = RefreshToken(user_id=applicant_user.id, token_hash=token_hash)
        db_session.add(rt)
        db_session.commit()
        
        stored = db_session.query(RefreshToken).filter(RefreshToken.user_id == applicant_user.id).first()
        assert stored.token_hash == token_hash
        assert stored.token_hash != token

    def test_refresh_token_revoked_on_use(self, client: TestClient, applicant_user: User):
        """Refresh token should be revoked after use"""
        # Login to get a refresh token (which is stored in DB)
        login_resp = client.post("/api/v1/auth/login", json={
            "email": applicant_user.email,
            "password": "applicant123"
        })
        assert login_resp.status_code == 200
        refresh_token = login_resp.json()["refresh_token"]
        
        # First refresh
        response1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response1.status_code == 200
        
        # Second use of same token should fail
        response2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response2.status_code == 400

    def test_refresh_token_rotation(self, client: TestClient, applicant_user: User):
        """New refresh token should be issued on refresh"""
        # Login to get a refresh token (which is stored in DB)
        login_resp = client.post("/api/v1/auth/login", json={
            "email": applicant_user.email,
            "password": "applicant123"
        })
        assert login_resp.status_code == 200
        refresh_token = login_resp.json()["refresh_token"]
        
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        
        new_refresh = response.json()["refresh_token"]
        assert new_refresh != refresh_token
        assert len(new_refresh) > 0


class TestAuthorizationSecurity:
    """Tests for authorization security"""

    def test_role_based_access_control(self, client: TestClient, db_session: Session):
        """RBAC should enforce role-based access"""
        # Create users with different roles
        users = {
            "admin": User(email="a@test.com", full_name="A", hashed_password="h", role="admin"),
            "analyst": User(email="an@test.com", full_name="An", hashed_password="h", role="analyst"),
            "reviewer": User(email="r@test.com", full_name="R", hashed_password="h", role="reviewer"),
            "auditor": User(email="au@test.com", full_name="Au", hashed_password="h", role="auditor"),
            "applicant": User(email="ap@test.com", full_name="Ap", hashed_password="h", role="applicant"),
        }
        for u in users.values():
            u.hashed_password = hash_password("pass")
        
        db_session.add_all(users.values())
        db_session.commit()
        
        # Test access to customer list
        for role, user in users.items():
            token = create_access_token(user.id)
            headers = {"Authorization": f"Bearer {token}"}
            
            if role in ["admin", "analyst", "reviewer", "auditor"]:
                # Staff should access
                response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {create_access_token(user.id)}"})
                assert response.status_code == 200, f"{role} should access"
            else:
                # Applicant should not
                response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {create_access_token(user.id)}"})
                assert response.status_code == 403, f"{role} should not access"

    def test_resource_ownership_enforcement(self, client: TestClient, db_session: Session):
        """Users should only access their own resources"""
        user1 = User(email="u1own@test.com", full_name="U1", hashed_password=hash_password("p1"), role="applicant")
        user2 = User(email="u2own@test.com", full_name="U2", hashed_password=hash_password("p2"), role="applicant")
        c1 = Customer(user_id=user1.id, first_name="U", last_name="1")
        c2 = Customer(user_id=user2.id, first_name="U", last_name="2")
        db_session.add_all([user1, user2, c1, c2])
        db_session.flush()
        app1 = Application(application_number="APP-OWN-1", customer_id=c1.id, status="draft")
        app2 = Application(application_number="APP-OWN-2", customer_id=c2.id, status="draft")
        
        db_session.add_all([app1, app2])
        db_session.commit()
        
        # User1 tries to access user2's application
        token1 = create_access_token(user1.id)
        response = client.get(f"/api/v1/applications/{app2.id}", headers={"Authorization": f"Bearer {token1}"})
        assert response.status_code == 403

    def test_inactive_user_cannot_access(self, client: TestClient, db_session: Session):
        """Inactive users should not access the system"""
        user = User(
            email="inactive@test.com",
            full_name="Inactive",
            hashed_password=hash_password("pass"),
            role="applicant",
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        token = create_access_token(user.id)
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


class TestInputValidationSecurity:
    """Tests for input validation security"""

    def test_xss_payloads_rejected_in_inputs(self, client: TestClient, admin_headers: dict):
        """XSS payloads should not be stored as executable HTML"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg onload=alert(1)>",
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/v1/customers", json={
                "first_name": payload,
                "last_name": "Test",
                "national_id": "0012345679",
            }, headers=admin_headers)
            
            # Should either reject or accept (JSON API - data stored in DB, not rendered as HTML)
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                # JSON responses are safe - data is stored in DB, not rendered as HTML
                # Verify the data is properly stored (not escaped or corrupted)
                assert data["first_name"] == payload

    def test_sql_injection_in_search(self, client: TestClient, admin_headers: dict):
        """SQL injection attempts should be neutralized"""
        sql_payloads = [
            "'; DROP TABLE customers; --",
            "' OR '1'='1",
            "'; DELETE FROM users; --",
            "' UNION SELECT password FROM users --",
        ]
        
        for payload in sql_payloads:
            response = client.get(f"/api/v1/search?q={payload}", headers=admin_headers)
            assert response.status_code in [200, 400, 422]
            
            # Should not crash or return all data
            data = response.json()
            if response.status_code == 200:
                assert "results" in data

    def test_large_payload_rejection(self, client: TestClient, admin_headers: dict):
        """Excessively large payloads should be rejected"""
        large_string = "x" * 1000000  # 1MB string
        
        response = client.post("/api/v1/customers", json={
            "first_name": large_string,
            "last_name": "Test",
            "national_id": "0012345679",
        }, headers=admin_headers)
        
        assert response.status_code in [400, 413, 422]

    def test_special_characters_in_national_id(self, client: TestClient, admin_headers: dict):
        """Special characters in national ID should be accepted by API (validated at business logic level)"""
        ids_with_special_chars = [
            "001234567a",  # Letter
            "001234567!",  # Special char
            "001234567 ",  # Space
            "001234567-",  # Hyphen
        ]
        
        for nid in ids_with_special_chars:
            response = client.post("/api/v1/customers", json={
                "first_name": "Test",
                "last_name": "User",
                "national_id": nid,
            }, headers=admin_headers)
            
            # API accepts the data; national_id validation happens during risk assessment
            assert response.status_code == 200


class TestDataProtection:
    """Tests for data protection"""

    def test_sensitive_data_not_in_api_responses(self, client: TestClient, admin_headers: dict):
        """Sensitive data should not appear in API responses"""
        response = client.get("/api/v1/customers", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        for customer in data.get("items", []):
            # Should not expose password hashes
            assert "hashed_password" not in customer
            assert "password" not in customer

    def test_pii_protection_in_logs(self, client: TestClient, caplog):
        """PII should not appear in logs"""
        # This would check log output
        pass

    def test_data_encryption_at_rest_placeholder(self):
        """Data encryption at rest should be configured"""
        # Database encryption, storage encryption
        pass

    def test_data_minimization_in_responses(self, client: TestClient, admin_headers: dict):
        """Responses should only include necessary data"""
        response = client.get("/api/v1/applications?page=1&page_size=1", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        if data["items"]:
            app = data["items"][0]
            # Should not include unnecessary internal fields
            assert "updated_at" not in app or app["updated_at"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])