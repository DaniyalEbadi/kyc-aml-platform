"""
Unit tests for domain/decisions.py - Deterministic decision boundary
These tests ensure the decision engine never delegates final approve/reject to LLM.
"""
from __future__ import annotations

import pytest
from app.domain.decisions import decide, DecisionOutcome, DecisionCode
from app.domain.rules import ValidationBundle, CheckResult
from app.domain.enums import RiskLevel


class TestSanctionsMatchForcesUnderReview:
    """Sanctions match must always force UNDER_REVIEW"""

    def test_sanctions_match_returns_under_review(self):
        bundle = ValidationBundle(checks=[])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=True)
        assert outcome.code == DecisionCode.UNDER_REVIEW
        assert outcome.auto is True
        assert "تحریم" in outcome.reason

    def test_sanctions_overrides_low_risk(self):
        """Even with LOW risk, sanctions forces review"""
        bundle = ValidationBundle(checks=[])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=True)
        assert outcome.code == DecisionCode.UNDER_REVIEW

    def test_sanctions_overrides_approved_bundle(self):
        """Even with clean validation, sanctions forces review"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=True)
        assert outcome.code == DecisionCode.UNDER_REVIEW


class TestPEPMatchForcesUnderReview:
    """PEP match must always force UNDER_REVIEW"""

    def test_pep_match_returns_under_review(self):
        bundle = ValidationBundle(checks=[])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=True, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW
        assert outcome.auto is True
        assert "اشخاص سیاسی" in outcome.reason

    def test_pep_overrides_low_risk(self):
        """Even with LOW risk, PEP forces review"""
        bundle = ValidationBundle(checks=[])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=True, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW


class TestCriticalRiskForcesUnderReview:
    """CRITICAL risk level must always force UNDER_REVIEW"""

    def test_critical_risk_returns_under_review(self):
        bundle = ValidationBundle(checks=[])
        outcome = decide(bundle, RiskLevel.CRITICAL, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW
        assert outcome.auto is True
        assert "ریسک بحرانی" in outcome.reason

    def test_critical_overrides_clean_validation(self):
        """Even with clean validation, CRITICAL forces review"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        outcome = decide(bundle, RiskLevel.CRITICAL, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW


class TestHighRiskForcesUnderReview:
    """HIGH risk level must force UNDER_REVIEW"""

    def test_high_risk_returns_under_review(self):
        bundle = ValidationBundle(checks=[])
        outcome = decide(bundle, RiskLevel.HIGH, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW
        assert outcome.auto is True

    def test_high_with_escalation_flag(self):
        """HIGH risk with bundle escalation also UNDER_REVIEW"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, escalate=True)])
        outcome = decide(bundle, RiskLevel.HIGH, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW


class TestResubmissionRequired:
    """Resubmission required cases"""

    def test_bundle_requires_resubmission(self):
        """Bundle with resubmit flag should return RESUBMISSION_REQUESTED"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.RESUBMISSION_REQUESTED
        assert outcome.auto is True
        assert "ارسال مجدد" in outcome.reason

    def test_resubmission_not_override_by_risk(self):
        """Resubmission should be returned even if risk is LOW/MEDIUM"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        for level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            outcome = decide(bundle, level, pep_match=False, sanctions_match=False)
            assert outcome.code == DecisionCode.RESUBMISSION_REQUESTED


class TestAutoApproval:
    """Cases where auto-approval is granted"""

    def test_low_risk_clean_bundle_approved(self):
        """LOW risk with clean validation should be APPROVED"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.APPROVED
        assert outcome.auto is True
        assert "تأیید خودکار" in outcome.reason

    def test_medium_risk_clean_bundle_approved(self):
        """MEDIUM risk with clean validation should be APPROVED"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        outcome = decide(bundle, RiskLevel.MEDIUM, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.APPROVED
        assert outcome.auto is True

    def test_approval_reason_mentions_policy_engine(self):
        """Approval reason should mention policy engine"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=False)
        assert "بررسی‌های قطعی" in outcome.reason


class TestDecisionPriorityOrder:
    """Tests that decision priorities are correctly ordered"""

    def test_sanctions_highest_priority(self):
        """Sanctions should override everything"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        outcome = decide(bundle, RiskLevel.CRITICAL, pep_match=True, sanctions_match=True)
        assert outcome.code == DecisionCode.UNDER_REVIEW

    def test_pep_overrides_resubmission(self):
        """PEP should override resubmission"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=True, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW

    def test_critical_overrides_resubmission(self):
        """CRITICAL should override resubmission"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        outcome = decide(bundle, RiskLevel.CRITICAL, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW

    def test_high_overrides_resubmission(self):
        """HIGH should override resubmission"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        outcome = decide(bundle, RiskLevel.HIGH, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.UNDER_REVIEW

    def test_resubmission_overrides_approval(self):
        """Resubmission should override approval"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, resubmit=True)])
        outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=False)
        assert outcome.code == DecisionCode.RESUBMISSION_REQUESTED


class TestDecisionOutcomeSerialization:
    """Tests for DecisionOutcome serialization"""

    def test_to_dict_includes_all_fields(self):
        outcome = DecisionOutcome(
            code=DecisionCode.APPROVED,
            reason="Test reason",
            auto=True
        )
        d = outcome.to_dict()
        assert d["code"] == "approved"
        assert d["reason"] == "Test reason"
        assert d["auto"] is True

    def test_decision_code_enum_values(self):
        """DecisionCode enum should have correct values"""
        assert DecisionCode.APPROVED.value == "approved"
        assert DecisionCode.REJECTED.value == "rejected"
        assert DecisionCode.RESUBMISSION_REQUESTED.value == "resubmission_requested"
        assert DecisionCode.UNDER_REVIEW.value == "under_review_by_specialist"


class TestLLMNeverDecides:
    """Critical tests ensuring LLM never makes final decisions"""

    def test_decide_function_is_deterministic(self):
        """Same inputs should always produce same output"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        for _ in range(100):
            outcome = decide(bundle, RiskLevel.LOW, pep_match=False, sanctions_match=False)
            assert outcome.code == DecisionCode.APPROVED

    def test_no_randomness_in_decision(self):
        """Decision should not use randomness"""
        bundle = ValidationBundle(checks=[CheckResult("c", True)])
        outcomes = [decide(bundle, RiskLevel.LOW, False, False).code for _ in range(1000)]
        assert all(o == DecisionCode.APPROVED for o in outcomes)

    def test_decision_boundary_documented(self):
        """The decision boundary logic should be explicit in code"""
        # This test documents the expected priority order:
        # 1. Sanctions match -> UNDER_REVIEW
        # 2. PEP match -> UNDER_REVIEW
        # 3. CRITICAL risk -> UNDER_REVIEW
        # 4. HIGH risk -> UNDER_REVIEW
        # 5. Bundle escalation -> UNDER_REVIEW
        # 6. Bundle resubmission -> RESUBMISSION_REQUESTED
        # 7. Else -> APPROVED
        # REJECTED is never returned by decide()
        
        # Verify REJECTED is never auto-returned
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
                            assert outcome.code != DecisionCode.REJECTED, \
                                f"REJECTED should never be auto-returned: level={level}, pep={pep}, sanctions={sanctions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])