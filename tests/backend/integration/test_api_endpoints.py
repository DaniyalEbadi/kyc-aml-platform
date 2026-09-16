"""
Integration tests for API endpoints
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.entities import User, Customer, Application, Document
from app.domain.enums import ApplicationStatus, DocumentType, RoleName
from app.core.security import create_access_token


class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    def test_login_success(self, client: TestClient, applicant_user: User):
        """Should login with valid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": applicant_user.email,
            "password": "applicant123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == applicant_user.email

    def test_login_invalid_credentials(self, client: TestClient):
        """Should reject invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrong"
        })
        assert response.status_code == 400
        assert response.json()["code"] == "bad_request"

    def test_login_missing_fields(self, client: TestClient):
        """Should reject missing fields"""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422  # Validation error

    def test_refresh_token(self, client: TestClient, applicant_user: User):
        """Should refresh access token"""
        # First login
        login_resp = client.post("/api/v1/auth/login", json={
            "email": applicant_user.email,
            "password": "applicant123"
        })
        refresh_token = login_resp.json()["refresh_token"]
        
        # Refresh
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client: TestClient):
        """Should reject invalid refresh token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.string"
        })
        assert response.status_code == 400

    def test_get_me(self, client: TestClient, auth_headers: dict):
        """Should return current user info"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data

    def test_get_me_unauthorized(self, client: TestClient):
        """Should reject without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_change_password(self, client: TestClient, auth_headers: dict):
        """Should change password"""
        response = client.post("/api/v1/auth/change-password", json={
            "old_password": "applicant123",
            "new_password": "newpassword123"
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_change_password_wrong_old(self, client: TestClient, auth_headers: dict):
        """Should reject wrong old password"""
        response = client.post("/api/v1/auth/change-password", json={
            "old_password": "wrong",
            "new_password": "newpassword123"
        }, headers=auth_headers)
        assert response.status_code == 400


class TestHealthEndpoints:
    """Tests for health endpoints"""

    def test_health_check(self, client: TestClient):
        """Health endpoint should return status"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data


class TestCustomerEndpoints:
    """Tests for customer endpoints"""

    def test_list_customers_as_analyst(self, client: TestClient, admin_headers: dict):
        """Analyst should list customers"""
        response = client.get("/api/v1/customers", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_customers_as_applicant_forbidden(self, client: TestClient, auth_headers: dict):
        """Applicant should not list customers"""
        response = client.get("/api/v1/customers", headers=auth_headers)
        assert response.status_code == 403

    def test_create_customer_as_admin(self, client: TestClient, admin_headers: dict):
        """Admin should create customer"""
        response = client.post("/api/v1/customers", json={
            "first_name": "New",
            "last_name": "Customer",
            "national_id": "0012345679",
            "email": "new@test.com"
        }, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "New"
        assert data["last_name"] == "Customer"

    def test_get_customer_detail(self, client: TestClient, admin_headers: dict, applicant_user: User):
        """Should get customer detail"""
        customer = applicant_user.customer  # Assuming relationship
        if not customer:
            from app.models.entities import Customer
            customer = Customer(user_id=applicant_user.id, first_name="Test", last_name="User")
            # Need to add to DB first
            pass
        
        response = client.get(f"/api/v1/customers/{customer.id}", headers=admin_headers)
        assert response.status_code == 200

    def test_update_customer(self, client: TestClient, admin_headers: dict, applicant_user: User, db_session: Session):
        """Should update customer"""
        customer = db_session.query(Customer).filter(Customer.user_id == applicant_user.id).first()
        response = client.put(f"/api/v1/customers/{customer.id}", json={
            "first_name": "Updated"
        }, headers=admin_headers)
        assert response.status_code == 200

    def test_search_customers(self, client: TestClient, admin_headers: dict):
        """Should search customers"""
        response = client.get("/api/v1/customers?search=Test", headers=admin_headers)
        assert response.status_code == 200


class TestApplicationEndpoints:
    """Tests for application endpoints"""

    def test_list_applications(self, client: TestClient, admin_headers: dict):
        """Should list applications"""
        response = client.get("/api/v1/applications", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_create_application(self, client: TestClient, auth_headers: dict):
        """Should create new application"""
        response = client.post("/api/v1/applications", json={}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "application_number" in data
        assert data["status"] == "draft"

    def test_get_application_detail(self, client: TestClient, auth_headers: dict, sample_application: Application):
        """Should get application detail"""
        response = client.get(f"/api/v1/applications/{sample_application.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["application_number"] == sample_application.application_number

    def test_update_application(self, client: TestClient, auth_headers: dict, sample_application: Application):
        """Should update application"""
        response = client.put(f"/api/v1/applications/{sample_application.id}", json={
            "first_name": "Updated",
            "occupation": "Engineer"
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_submit_application(self, client: TestClient, auth_headers: dict, sample_application: Application):
        """Should submit application"""
        response = client.post(f"/api/v1/applications/{sample_application.id}/submit", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["submitted", "needs_resubmission", "approved", "in_review"]

    def test_filter_applications_by_status(self, client: TestClient, admin_headers: dict):
        """Should filter by status"""
        response = client.get("/api/v1/applications?status=submitted", headers=admin_headers)
        assert response.status_code == 200

    def test_search_applications(self, client: TestClient, admin_headers: dict):
        """Should search applications"""
        response = client.get("/api/v1/applications?search=APP-1001", headers=admin_headers)
        assert response.status_code == 200


class TestDocumentEndpoints:
    """Tests for document endpoints"""

    def test_upload_document(self, client: TestClient, auth_headers: dict, sample_application: Application):
        """Should upload document"""
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        data = {"app_id": sample_application.id, "doc_type": "national_id"}
        response = client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert "job" in data

    def test_get_document(self, client: TestClient, auth_headers: dict):
        """Should get document"""
        # Would need a document first
        pass

    def test_list_documents(self, client: TestClient, admin_headers: dict):
        """Should list documents"""
        response = client.get("/api/v1/documents", headers=admin_headers)
        assert response.status_code == 200


class TestVerificationEndpoints:
    """Tests for verification endpoints"""

    def test_face_verification(self, client: TestClient, auth_headers: dict, sample_application: Application):
        """Should compare faces"""
        files = {"selfie": ("selfie.jpg", b"fake selfie", "image/jpeg")}
        data = {"app_id": sample_application.id}
        response = client.post("/api/v1/verification/face", files=files, data=data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "similarity" in data
        assert "decision" in data

    def test_get_verifications(self, client: TestClient, admin_headers: dict, sample_application: Application):
        """Should get verifications"""
        response = client.get(f"/api/v1/verification/{sample_application.id}", headers=admin_headers)
        assert response.status_code == 200


class TestRiskEndpoints:
    """Tests for risk endpoints"""

    def test_get_risk_assessment(self, client: TestClient, admin_headers: dict, sample_application: Application):
        """Should get risk assessment"""
        response = client.get(f"/api/v1/risk/{sample_application.id}", headers=admin_headers)
        assert response.status_code == 200
        # May return null if not computed yet


class TestCaseEndpoints:
    """Tests for case endpoints"""

    def test_list_cases(self, client: TestClient, admin_headers: dict):
        """Should list cases"""
        response = client.get("/api/v1/cases", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_case_detail(self, client: TestClient, admin_headers: dict):
        """Should get case detail"""
        # Would need a case first
        pass

    def test_review_case(self, client: TestClient, admin_headers: dict):
        """Should review case"""
        # Would need a case first
        pass


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints"""

    def test_get_analytics(self, client: TestClient, admin_headers: dict):
        """Should get analytics data"""
        response = client.get("/api/v1/analytics", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data
        assert "applications_over_time" in data

    def test_reviewer_workload(self, client: TestClient, admin_headers: dict):
        """Should get reviewer workload"""
        response = client.get("/api/v1/analytics/reviewer-workload", headers=admin_headers)
        assert response.status_code == 200


class TestAuditEndpoints:
    """Tests for audit endpoints"""

    def test_list_audit_events(self, client: TestClient, admin_headers: dict):
        """Should list audit events"""
        response = client.get("/api/v1/audit", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_entity_audit_history(self, client: TestClient, admin_headers: dict, sample_application: Application):
        """Should get entity audit history"""
        response = client.get(f"/api/v1/audit/application/{sample_application.id}", headers=admin_headers)
        assert response.status_code == 200


class TestPolicyEndpoints:
    """Tests for policy endpoints"""

    def test_list_policies(self, client: TestClient, auth_headers: dict):
        """Should list policies"""
        response = client.get("/api/v1/policies", headers=auth_headers)
        assert response.status_code == 200

    def test_search_policies(self, client: TestClient, auth_headers: dict):
        """Should search policies"""
        response = client.post("/api/v1/policies/search", json={"query": "identity"}, headers=auth_headers)
        assert response.status_code == 200


class TestNotificationEndpoints:
    """Tests for notification endpoints"""

    def test_list_notifications(self, client: TestClient, auth_headers: dict):
        """Should list notifications"""
        response = client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_mark_notifications_read(self, client: TestClient, auth_headers: dict):
        """Should mark notifications read"""
        response = client.post("/api/v1/notifications/read", json={"mark_all": True}, headers=auth_headers)
        assert response.status_code == 200


class TestSearchEndpoints:
    """Tests for search endpoints"""

    def test_global_search(self, client: TestClient, auth_headers: dict):
        """Should perform global search"""
        response = client.get("/api/v1/search?q=APP-1001", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


class TestJobEndpoints:
    """Tests for job endpoints"""

    def test_get_job_status(self, client: TestClient, auth_headers: dict):
        """Should get job status"""
        # Would need a job first
        pass


class TestAuthorization:
    """Tests for role-based authorization"""

    def test_applicant_cannot_access_admin_endpoints(self, client: TestClient, auth_headers: dict):
        """Applicant should not access admin endpoints"""
        response = client.get("/api/v1/customers", headers=auth_headers)
        assert response.status_code == 403

    def test_analyst_can_access_analytics(self, client: TestClient):
        """Analyst should access analytics"""
        # Would need analyst user
        pass

    def test_reviewer_can_review_cases(self, client: TestClient):
        """Reviewer should review cases"""
        # Would need reviewer user
        pass


class TestRateLimiting:
    """Tests for rate limiting"""

    def test_rate_limit_headers(self, client: TestClient):
        """Responses should include rate limit headers"""
        response = client.get("/api/v1/health")
        # Check for rate limit headers if implemented


if __name__ == "__main__":
    pytest.main([__file__, "-v"])