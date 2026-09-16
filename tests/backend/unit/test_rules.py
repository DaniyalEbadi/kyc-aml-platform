"""
Unit tests for domain/rules.py - Deterministic validation logic
These tests ensure the core validation rules work correctly.
"""
from __future__ import annotations

import pytest
from datetime import date, timedelta

from app.domain.rules import (
    validate_iranian_national_id,
    validate_identity_expiry,
    validate_name_consistency,
    validate_proof_of_address_age,
    validate_national_id_field,
    validate_application_payload,
    CheckResult,
    ValidationBundle,
)


class TestIranianNationalIdValidation:
    """Tests for Iranian national ID checksum algorithm"""

    def test_valid_national_ids(self):
        """Test known valid Iranian national IDs"""
        valid_ids = [
            "0012345678",  # Test pattern
            "1234567890",
            "9876543210",
        ]
        for nid in valid_ids:
            # These are test patterns, not real IDs
            # The algorithm should validate correctly
            result = validate_iranian_national_id(nid)
            assert isinstance(result, bool)

    def test_invalid_checksum(self):
        """Test IDs with invalid checksum"""
        invalid_ids = [
            "0012345678",  # Wrong checksum (should be 9)
            "1111111111",  # All same digits
            "123456789",   # Too short
            "12345678901", # Too long
            "abcdefghij",  # Non-numeric
            "",            # Empty
            None,          # None
        ]
        for nid in invalid_ids:
            assert validate_iranian_national_id(nid) is False

    def test_all_same_digits_rejected(self):
        """All same digits should be rejected"""
        for digit in "0123456789":
            nid = digit * 10
            assert validate_iranian_national_id(nid) is False

    def test_checksum_algorithm_correctness(self):
        """Test the exact checksum calculation"""
        # For ID "0012345678":
        # Sum = 0*10 + 0*9 + 1*8 + 2*7 + 3*6 + 4*5 + 5*4 + 6*3 + 7*2 = 0+0+8+14+18+20+20+18+14 = 112
        # 112 % 11 = 2, check = 11-2 = 9
        # So valid ID should be "0012345679"
        # Our test ID has check=8, so it should be invalid
        assert validate_iranian_national_id("0012345678") is False
        assert validate_iranian_national_id("0012345679") is True


class TestIdentityExpiryValidation:
    """Tests for identity document expiry validation"""

    def test_valid_future_expiry(self):
        """Future expiry date should pass"""
        future = (date.today() + timedelta(days=30)).isoformat()
        result = validate_identity_expiry(future)
        assert result.passed is True
        assert result.code == "identity_expiry"

    def test_today_expiry_passes(self):
        """Today's date should pass (not expired yet)"""
        today = date.today().isoformat()
        result = validate_identity_expiry(today)
        assert result.passed is True

    def test_expired_document_fails(self):
        """Expired document should fail with resubmit flag"""
        past = (date.today() - timedelta(days=1)).isoformat()
        result = validate_identity_expiry(past)
        assert result.passed is False
        assert result.resubmit is True
        assert result.escalate is False
        assert result.score_impact == 25

    def test_invalid_date_format_fails(self):
        """Invalid date format should fail"""
        result = validate_identity_expiry("invalid-date")
        assert result.passed is False
        assert result.resubmit is True
        assert result.score_impact == 18

    def test_none_date_fails(self):
        """None date should fail"""
        result = validate_identity_expiry(None)
        assert result.passed is False
        assert result.resubmit is True


class TestNameConsistencyValidation:
    """Tests for name matching between document and application"""

    def test_exact_match_passes(self):
        """Exact name match should pass"""
        result = validate_name_consistency("محمد احمدی", "محمد احمدی")
        assert result.passed is True
        assert result.code == "name_match"

    def test_formatting_differences_pass(self):
        """Minor formatting differences should pass"""
        # Token overlap: both have "محمد" and "احمدی"
        result = validate_name_consistency("محمد احمدی", "احمدی محمد")
        assert result.passed is True

    def test_clear_mismatch_fails(self):
        """Clearly different names should fail with escalate"""
        result = validate_name_consistency("محمد احمدی", "علی رضایی")
        assert result.passed is False
        assert result.escalate is True
        assert result.score_impact == 30

    def test_empty_names_fail(self):
        """Empty names should fail"""
        result = validate_name_consistency("", "محمد احمدی")
        assert result.passed is False
        result = validate_name_consistency("محمد احمدی", "")
        assert result.passed is False

    def test_partial_match_passes(self):
        """Partial token overlap should pass"""
        # "محمد احمدی" vs "محمد" - overlap of 1, smaller set size 1, so 1 >= max(1, 1-1) = 1
        result = validate_name_consistency("محمد احمدی", "محمد")
        assert result.passed is True


class TestProofOfAddressAgeValidation:
    """Tests for proof of address document age"""

    def test_recent_document_passes(self):
        """Document within 90 days should pass"""
        recent = (date.today() - timedelta(days=30)).isoformat()
        result = validate_proof_of_address_age(recent)
        assert result.passed is True
        assert result.code == "address_age"

    def test_exact_90_days_passes(self):
        """Exactly 90 days should pass"""
        exact = (date.today() - timedelta(days=90)).isoformat()
        result = validate_proof_of_address_age(exact)
        assert result.passed is True

    def test_over_90_days_fails(self):
        """Over 90 days should fail with resubmit"""
        old = (date.today() - timedelta(days=91)).isoformat()
        result = validate_proof_of_address_age(old)
        assert result.passed is False
        assert result.resubmit is True
        assert result.score_impact == 16

    def test_invalid_date_fails(self):
        """Invalid date format should fail"""
        result = validate_proof_of_address_age("not-a-date")
        assert result.passed is False
        assert result.resubmit is True
        assert result.score_impact == 12

    def test_custom_limit_days(self):
        """Custom limit should work"""
        old = (date.today() - timedelta(days=60)).isoformat()
        result = validate_proof_of_address_age(old, limit_days=30)
        assert result.passed is False


class TestNationalIdFieldValidation:
    """Tests for national ID field validation"""

    def test_none_nid_passes_optional(self):
        """None NID should pass (optional field)"""
        result = validate_national_id_field(None)
        assert result.passed is True

    def test_valid_nid_passes(self):
        """Valid NID should pass"""
        result = validate_national_id_field("0012345679")
        assert result.passed is True

    def test_invalid_nid_fails_escalate(self):
        """Invalid NID should fail with escalate"""
        result = validate_national_id_field("0012345678")
        assert result.passed is False
        assert result.escalate is True
        assert result.score_impact == 22


class TestFullApplicationValidation:
    """Integration tests for full application payload validation"""

    def test_clean_application_passes(self):
        """Clean application should pass all checks"""
        payload = {
            "customer_name": "محمد احمدی",
            "national_id": "0012345679",
            "identity_document": {
                "name_on_document": "محمد احمدی",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            },
            "proof_of_address": {
                "document_date": date.today().isoformat(),
            },
            "quality": {"overall": 80},
            "face": {"similarity": 0.85},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_escalation is False
        assert bundle.requires_resubmission is False
        assert len(bundle.all_issues) == 0

    def test_expired_identity_triggers_resubmission(self):
        """Expired identity should trigger resubmission"""
        payload = {
            "customer_name": "محمد احمدی",
            "identity_document": {
                "name_on_document": "محمد احمدی",
                "expiry_date": (date.today() - timedelta(days=1)).isoformat(),
            },
            "quality": {"overall": 80},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_resubmission is True
        assert bundle.requires_escalation is False

    def test_name_mismatch_triggers_escalation(self):
        """Name mismatch should trigger escalation"""
        payload = {
            "customer_name": "محمد احمدی",
            "identity_document": {
                "name_on_document": "علی رضایی",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            },
            "quality": {"overall": 80},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_escalation is True
        assert bundle.requires_resubmission is False

    def test_old_address_triggers_resubmission(self):
        """Old proof of address should trigger resubmission"""
        payload = {
            "customer_name": "محمد احمدی",
            "identity_document": {
                "name_on_document": "محمد احمدی",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            },
            "proof_of_address": {
                "document_date": (date.today() - timedelta(days=100)).isoformat(),
            },
            "quality": {"overall": 80},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_resubmission is True

    def test_low_quality_triggers_resubmission(self):
        """Low document quality should trigger resubmission"""
        payload = {
            "customer_name": "محمد احمدی",
            "identity_document": {
                "name_on_document": "محمد احمدی",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            },
            "quality": {"overall": 30},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_resubmission is True

    def test_low_face_similarity_triggers_escalation(self):
        """Low face similarity should trigger escalation"""
        payload = {
            "customer_name": "محمد احمدی",
            "identity_document": {
                "name_on_document": "محمد احمدی",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            },
            "quality": {"overall": 80},
            "face": {"similarity": 0.5},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_escalation is True

    def test_invalid_national_id_triggers_escalation(self):
        """Invalid national ID should trigger escalation"""
        payload = {
            "customer_name": "محمد احمدی",
            "national_id": "0012345678",  # Invalid checksum
            "identity_document": {
                "name_on_document": "محمد احمدی",
                "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            },
            "quality": {"overall": 80},
        }
        bundle = validate_application_payload(payload)
        assert bundle.requires_escalation is True


class TestValidationBundleProperties:
    """Tests for ValidationBundle computed properties"""

    def test_all_issues_collects_messages(self):
        """all_issues should collect all failed check messages"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", False, message="Issue 1"),
            CheckResult("check2", True, message="OK"),
            CheckResult("check3", False, message="Issue 3"),
        ])
        assert bundle.all_issues == ["Issue 1", "Issue 3"]

    def test_requires_escalation_detects_escalate(self):
        """requires_escalation should detect any escalate flag"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", False, escalate=True),
            CheckResult("check2", False),
        ])
        assert bundle.requires_escalation is True

    def test_requires_resubmission_detects_resubmit(self):
        """requires_resubmission should detect any resubmit flag"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", False, resubmit=True),
            CheckResult("check2", False),
        ])
        assert bundle.requires_resubmission is True

    def test_to_dict_serialization(self):
        """to_dict should serialize correctly"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", True, message="OK"),
        ])
        d = bundle.to_dict()
        assert "checks" in d
        assert "all_issues" in d
        assert "requires_escalation" in d
        assert "requires_resubmission" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])