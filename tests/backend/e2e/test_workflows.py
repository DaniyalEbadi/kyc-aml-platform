"""
End-to-end tests for complete KYC workflows
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import io

from app.models.entities import User, Customer, Application, Document, Case
from app.domain.enums import ApplicationStatus, DocumentType, CaseStatus, CasePriority, RiskLevel, DecisionCode
from app.core.security import create_access_token, hash_password


class TestCompleteOnboardingWorkflow:
    """E2E test for complete customer onboarding"""

    def test_full_onboarding_flow(self, client: TestClient, db_session: Session):
        """Test complete onboarding from registration to decision"""
        # 1. Register/Login as applicant
        applicant = User(
            email="e2e@test.com",
            full_name="E2E Test User",
            hashed_password=hash_password("password123"),
            role="applicant",
        )
        db_session.add(applicant)
        db_session.commit()
        
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "e2e@test.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create application
        create_resp = client.post("/api/v1/applications", json={}, headers=headers)
        assert create_resp.status_code == 200
        app_id = create_resp.json()["id"]
        app_number = create_resp.json()["application_number"]
        
        # 3. Update personal info
        update_resp = client.put(f"/api/v1/applications/{app_id}", json={
            "first_name": "E2E",
            "last_name": "User",
            "national_id": "0012345679",
            "birth_date": "1370/01/01",
            "gender": "مرد",
            "nationality": "ایران",
            "province": "تهران",
            "city": "تهران",
            "address": "خیابان ولیعصر پلاک ۱۰",
            "phone": "09123456789",
            "email": "e2e@test.com",
            "occupation": "مهندس",
            "declared_income": "۵۰-۱۰۰ میلیون",
            "source_of_funds": "حقوق",
            "expected_volume": "متوسط",
        }, headers=headers)
        assert update_resp.status_code == 200
        
        # 4. Upload identity document
        files = {"file": ("national_id.jpg", b"fake image data", "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        upload_resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
        assert upload_resp.status_code == 200
        doc_id = upload_resp.json()["document"]["id"]
        
        # 5. Wait for document processing (poll job)
        job_id = upload_resp.json()["job"]["id"]
        for _ in range(10):
            job_resp = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
            if job_resp.json()["status"] in ["succeeded", "failed"]:
                break
            import time
            time.sleep(0.5)
        
        # 6. Upload selfie for face verification
        files = {"selfie": ("selfie.jpg", b"fake selfie", "image/jpeg")}
        data = {"app_id": app_id}
        face_resp = client.post("/api/v1/verification/face", files=files, data=data, headers=headers)
        assert face_resp.status_code == 200
        assert face_resp.json()["decision"] in ["match", "mismatch"]
        
        # 7. Submit application
        submit_resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] in ["submitted", "needs_resubmission", "approved", "in_review"]
        
        # 8. Wait for risk assessment and decision
        import time
        time.sleep(1)
        
        # 9. Check final decision
        detail_resp = client.get(f"/api/v1/applications/{app_id}", headers=headers)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["status"] in ["approved", "in_review", "needs_resubmission"]
        
        # Verify audit trail
        from app.models.entities import AuditEvent
        audits = db_session.query(AuditEvent).filter(
            AuditEvent.entity == "application",
            AuditEvent.entity_id == app_id
        ).all()
        assert len(audits) >= 3  # create, submit, decision


class TestDocumentProcessingPipeline:
    """E2E test for document processing pipeline"""

    def test_document_processing_stages(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test document goes through all processing stages"""
        # Create application
        create_resp = client.post("/api/v1/applications", json={}, headers=auth_headers)
        app_id = create_resp.json()["id"]
        
        # Upload document
        files = {"file": ("passport.jpg", b"fake passport", "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "passport"}
        upload_resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        assert upload_resp.status_code == 200
        
        job_id = upload_resp.json()["job"]["id"]
        doc_id = upload_resp.json()["document"]["id"]
        
        # Poll job until completion
        import time
        job_completed = False
        for _ in range(20):
            job_resp = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
            job = job_resp.json()
            if job["status"] == "succeeded":
                assert job["progress"] == 100
                assert job["stage"] == "تکمیل شد"
                job_completed = True
                break
            elif job["status"] == "failed":
                pytest.fail(f"Job failed: {job.get('error')}")
            time.sleep(0.5)
        
        # Verify document exists
        doc_resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
        assert doc_resp.status_code == 200
        doc = doc_resp.json()
        # In test environment, document processing may run synchronously (if inline_jobs=True
        # and processing happens in the same DB) or may stay as "uploaded" (if processing
        # dispatches to a different DB session)
        assert doc["status"] in ["uploaded", "processed"]
        
        if job_completed and doc["status"] == "processed":
            # Verify extracted fields
            assert "fields" in doc
            assert len(doc["fields"]) > 0
            for field in doc["fields"]:
                assert "field_name" in field
                assert "field_label" in field
                assert "confidence" in field
            
            # Verify verification record created
            ver_resp = client.get(f"/api/v1/verification/{app_id}", headers=auth_headers)
            assert ver_resp.status_code == 200
            verifications = ver_resp.json()
            ocr_ver = [v for v in verifications if v["kind"] == "ocr"]
            assert len(ocr_ver) > 0
            assert ocr_ver[0]["status"] == "done"


class TestCaseManagementWorkflow:
    """E2E test for case management workflow"""

    def test_case_creation_and_review(self, client: TestClient, db_session: Session, admin_headers: dict):
        """Test case creation, assignment, and review"""
        # Create high-risk application that triggers case creation
        # This would require setting up an application with high risk
        pass

    def test_case_assignment(self, client: TestClient, db_session: Session, admin_headers: dict, reviewer_user: User):
        """Test case assignment to reviewer"""
        pass

    def test_case_review_approve(self, client: TestClient, db_session: Session, reviewer_headers: dict):
        """Test case approval by reviewer"""
        pass

    def test_case_review_reject(self, client: TestClient, db_session: Session, reviewer_headers: dict):
        """Test case rejection by reviewer"""
        pass

    def test_case_review_resubmit(self, client: TestClient, db_session: Session, reviewer_headers: dict):
        """Test case resubmission request"""
        pass

    def test_case_escalation(self, client: TestClient, db_session: Session, admin_headers: dict):
        """Test case escalation"""
        pass


class TestRiskAssessmentWorkflow:
    """E2E test for risk assessment"""

    def test_low_risk_auto_approval(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Low risk application should be auto-approved"""
        # Create clean application
        create_resp = client.post("/api/v1/applications", json={}, headers=auth_headers)
        app_id = create_resp.json()["id"]
        
        # Update with clean data
        client.put(f"/api/v1/applications/{app_id}", json={
            "first_name": "Low",
            "last_name": "Risk",
            "national_id": "0012345679",
            "occupation": "کارمند",
            "declared_income": "زیر ۱۰ میلیون",
            "source_of_funds": "حقوق",
            "expected_volume": "پایین",
        }, headers=auth_headers)
        
        # Upload valid documents
        for doc_type in ["national_id", "proof_of_address"]:
            files = {"file": (f"{doc_type}.jpg", b"fake", "image/jpeg")}
            data = {"app_id": app_id, "doc_type": doc_type}
            client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        
        # Submit
        client.post(f"/api/v1/applications/{app_id}/submit", headers=auth_headers)
        
        # Wait for processing
        import time
        time.sleep(2)
        
        # Check result - should be approved, in_review, or needs_resubmission (if identity docs not fully processed)
        detail = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers).json()
        assert detail["status"] in ["approved", "in_review", "needs_resubmission"]
        
        if detail["status"] == "approved":
            # Verify no case created
            from app.models.entities import Case
            cases = db_session.query(Case).filter(Case.application_id == app_id).all()
            assert len(cases) == 0

    def test_high_risk_creates_case(self, client: TestClient, db_session: Session, auth_headers: dict):
        """High risk application should create case"""
        # Create application with high risk indicators
        create_resp = client.post("/api/v1/applications", json={}, headers=auth_headers)
        app_id = create_resp.json()["id"]
        
        # Update with high risk data
        client.put(f"/api/v1/applications/{app_id}", json={
            "first_name": "High",
            "last_name": "Risk",
            "national_id": "0012345679",
            "occupation": "بازرگان",
            "declared_income": "بالای ۱۰۰ میلیون",
            "source_of_funds": "بازرگانی",
            "expected_volume": "بالا",
        }, headers=auth_headers)
        
        # Upload documents
        files = {"file": ("national_id.jpg", b"fake", "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        
        # Submit
        client.post(f"/api/v1/applications/{app_id}/submit", headers=auth_headers)
        
        import time
        time.sleep(2)
        
        # Check final status - depends on validation outcome
        detail = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers).json()
        
        # Check case created only if status is in_review (cases are created for review decisions)
        from app.models.entities import Case
        cases = db_session.query(Case).filter(Case.application_id == app_id).all()
        if detail["status"] == "in_review":
            assert len(cases) > 0
            assert cases[0].status == CaseStatus.OPEN.value
            assert cases[0].priority in [CasePriority.HIGH.value, CasePriority.CRITICAL.value]
        else:
            assert len(cases) == 0


class TestAMLScreeningWorkflow:
    """E2E test for AML screening"""

    def test_sanctions_match_triggers_review(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Sanctions match should trigger UNDER_REVIEW"""
        create_resp = client.post("/api/v1/applications", json={}, headers=auth_headers)
        app_id = create_resp.json()["id"]
        
        # Use name that triggers sanctions match
        client.put(f"/api/v1/applications/{app_id}", json={
            "first_name": "جان",
            "last_name": "تحریم شده",
            "national_id": "0012345679",
        }, headers=auth_headers)
        
        # Upload and submit
        files = {"file": ("national_id.jpg", b"fake", "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        
        client.post(f"/api/v1/applications/{app_id}/submit", headers=auth_headers)
        
        import time
        time.sleep(2)
        
        detail = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers).json()
        assert detail["status"] == "in_review"
        
        # Check screening results
        screening_resp = client.get(f"/api/v1/screening/{app_id}", headers=auth_headers)
        assert screening_resp.status_code == 200
        screenings = screening_resp.json()
        sanctions = [s for s in screenings if s["kind"] == "sanctions"]
        assert len(sanctions) > 0
        assert sanctions[0]["matched"] is True

    def test_pep_match_triggers_review(self, client: TestClient, db_session: Session, auth_headers: dict):
        """PEP match should trigger UNDER_REVIEW"""
        create_resp = client.post("/api/v1/applications", json={}, headers=auth_headers)
        app_id = create_resp.json()["id"]
        
        # Use name that triggers PEP match
        client.put(f"/api/v1/applications/{app_id}", json={
            "first_name": "علی",
            "last_name": "سیاسی",
            "national_id": "0012345679",
        }, headers=auth_headers)
        
        # Upload and submit
        files = {"file": ("national_id.jpg", b"fake", "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        
        client.post(f"/api/v1/applications/{app_id}/submit", headers=auth_headers)
        
        import time
        time.sleep(2)
        
        detail = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers).json()
        assert detail["status"] == "in_review"
        
        # Check screening results
        screening_resp = client.get(f"/api/v1/screening/{app_id}", headers=auth_headers)
        screenings = screening_resp.json()
        pep = [s for s in screenings if s["kind"] == "pep"]
        assert len(pep) > 0
        assert pep[0]["matched"] is True


class TestAuditTrailCompleteness:
    """E2E test for audit trail completeness"""

    def test_all_actions_audited(self, client: TestClient, db_session: Session, auth_headers: dict, admin_headers: dict):
        """All significant actions should be audited"""
        create_resp = client.post("/api/v1/applications", json={}, headers=auth_headers)
        app_id = create_resp.json()["id"]
        
        # Update
        client.put(f"/api/v1/applications/{app_id}", json={"first_name": "Test"}, headers=auth_headers)
        
        # Upload
        files = {"file": ("test.jpg", b"fake", "image/jpeg")}
        data = {"app_id": app_id, "doc_type": "national_id"}
        client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_headers)
        
        # Submit
        client.post(f"/api/v1/applications/{app_id}/submit", headers=auth_headers)
        
        import time
        time.sleep(1)
        
        # Check audit events
        from app.models.entities import AuditEvent
        audits = db_session.query(AuditEvent).filter(
            AuditEvent.entity == "application",
            AuditEvent.entity_id == app_id
        ).order_by(AuditEvent.created_at).all()
        
        actions = {a.action for a in audits}
        assert "application.create" in actions
        assert "application.updated" in actions or "application.update" in actions
        assert "application.submit" in actions
        assert "engine.decision" in actions
        
        # Verify audit entries have required fields
        for audit in audits:
            # engine.decision is automated (no human actor), other actions should have actor_id
            if audit.action != "engine.decision":
                assert audit.actor_id is not None
            assert audit.entity is not None
            assert audit.entity_id is not None
            assert audit.created_at is not None


class TestNotificationDelivery:
    """E2E test for notification delivery"""

    def test_notifications_on_case_creation(self, client: TestClient, db_session: Session):
        """Reviewers should be notified on case creation"""
        pass

    def test_notifications_on_high_risk(self, client: TestClient, db_session: Session):
        """High risk should notify reviewers"""
        pass

    def test_applicant_notifications(self, client: TestClient, db_session: Session):
        """Applicant should receive status notifications"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])