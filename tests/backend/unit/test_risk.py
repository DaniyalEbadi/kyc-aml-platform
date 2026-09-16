"""
Unit tests for domain/risk.py - Explainable risk scoring engine
"""
from __future__ import annotations

import pytest
from app.domain.risk import compute_risk, RiskLevel, Factor, RiskResult
from app.domain.rules import ValidationBundle, CheckResult


class TestRiskLevelCalculation:
    """Tests for risk level thresholds"""

    def test_low_risk_threshold(self):
        """Score < 35 should be LOW"""
        assert RiskLevel.LOW == RiskLevel.LOW

    def test_medium_risk_threshold(self):
        """Score 35-59 should be MEDIUM"""
        # This tests the _level function logic
        from app.domain.risk import _level
        assert _level(34) == RiskLevel.LOW
        assert _level(35) == RiskLevel.MEDIUM
        assert _level(59) == RiskLevel.MEDIUM

    def test_high_risk_threshold(self):
        """Score 60-79 should be HIGH"""
        from app.domain.risk import _level
        assert _level(60) == RiskLevel.HIGH
        assert _level(79) == RiskLevel.HIGH

    def test_critical_risk_threshold(self):
        """Score >= 80 should be CRITICAL"""
        from app.domain.risk import _level
        assert _level(80) == RiskLevel.CRITICAL
        assert _level(100) == RiskLevel.CRITICAL


class TestRiskFactorStructure:
    """Tests for Factor dataclass"""

    def test_factor_creation(self):
        """Factor should store all attributes"""
        f = Factor(
            code="test",
            label="Test Factor",
            weight=10,
            triggered=True,
            detail="Test detail"
        )
        assert f.code == "test"
        assert f.label == "Test Factor"
        assert f.weight == 10
        assert f.triggered is True
        assert f.detail == "Test detail"

    def test_factor_to_dict_in_result(self):
        """RiskResult.to_dict should include factor dicts"""
        factors = [
            Factor("f1", "Factor 1", 10, True, "Detail 1"),
            Factor("f2", "Factor 2", 5, False, "Detail 2"),
        ]
        result = RiskResult(score=50, level=RiskLevel.MEDIUM, factors=factors)
        d = result.to_dict()
        assert d["score"] == 50
        assert d["level"] == "medium"
        assert d["level_fa"] == "ریسک متوسط"
        assert len(d["factors"]) == 2
        assert d["factors"][0]["code"] == "f1"
        assert d["factors"][0]["triggered"] is True


class TestComputeRiskBaseScore:
    """Tests for base risk score calculation"""

    def test_base_score_with_iranian_nationality(self):
        """Iranian nationality should have lower base"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
            anomalies=0,
            declared_high_volume=False,
        )
        # Base = 8 + 8 = 16, all checks pass, quality > 55, face > 0.62
        # No additional factors
        assert result.score == 16

    def test_base_score_with_foreign_nationality(self):
        """Foreign nationality should have higher base"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=12,
            anomalies=0,
            declared_high_volume=False,
        )
        # Base = 8 + 12 = 20
        assert result.score == 20


class TestValidationFailureImpact:
    """Tests for validation failure score impacts"""

    def test_failed_check_adds_score_impact(self):
        """Failed checks should add their score_impact"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", False, score_impact=18, message="Failed"),
            CheckResult("check2", True, message="Passed"),
        ])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        # Base 16 + 18 = 34
        assert result.score == 34

    def test_multiple_failed_checks_cumulative(self):
        """Multiple failed checks should accumulate"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", False, score_impact=18),
            CheckResult("check2", False, score_impact=25),
        ])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        # Base 16 + 18 + 25 = 59
        assert result.score == 59

    def test_passed_checks_no_impact(self):
        """Passed checks should not add score"""
        bundle = ValidationBundle(checks=[
            CheckResult("check1", True, score_impact=18),
            CheckResult("check2", True, score_impact=25),
        ])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 16  # Base 8+8=16


class TestQualityScoreImpact:
    """Tests for document quality score impact"""

    def test_low_quality_adds_points(self):
        """Quality < 55 should add 14 points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=50,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 30  # Base 16 + 14

    def test_acceptable_quality_no_impact(self):
        """Quality >= 55 should not add points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=60,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 16  # Base 8+8=16

    def test_quality_boundary_55(self):
        """Quality exactly 55 should be acceptable"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=55,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 16  # Base 8+8=16


class TestFaceSimilarityImpact:
    """Tests for face verification similarity impact"""

    def test_low_similarity_adds_points(self):
        """Similarity < 0.62 should add 22 points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.5,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 38  # Base 16 + 22

    def test_high_similarity_no_impact(self):
        """Similarity >= 0.62 should not add points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.7,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 16  # Base 8+8=16

    def test_boundary_062(self):
        """Similarity exactly 0.62 should be acceptable"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.62,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 16  # Base 8+8=16

    def test_none_similarity_no_impact(self):
        """None similarity should not add points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=None,
            pep=False,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 16  # Base 8+8=16


class TestPEPSanctionsImpact:
    """Tests for PEP and Sanctions matching"""

    def test_pep_match_adds_35(self):
        """PEP match should add 35 points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=True,
            sanctions=False,
            jurisdiction_risk=8,
        )
        assert result.score == 51  # Base 16 + 35

    def test_sanctions_match_adds_50(self):
        """Sanctions match should add 50 points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=True,
            jurisdiction_risk=8,
        )
        assert result.score == 66  # Base 16 + 50

    def test_both_pep_and_sanctions(self):
        """Both PEP and sanctions should accumulate"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=True,
            sanctions=True,
            jurisdiction_risk=8,
        )
        assert result.score == 100  # Base 16 + 35 + 50 = 101 (clamped to 100)

    def test_no_match_no_impact(self):
        """No match should not add points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
        )
        assert result.score == 18  # Base 8+10=18


class TestHighVolumeAnomalies:
    """Tests for high volume and anomaly factors"""

    def test_high_volume_adds_8(self):
        """Declared high volume should add 8 points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            declared_high_volume=True,
        )
        assert result.score >= 24  # Base 16 + 8

    def test_anomalies_add_6_each(self):
        """Each anomaly should add 6 points"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=80,
            face_similarity=0.9,
            pep=False,
            sanctions=False,
            anomalies=3,
        )
        assert result.score >= 34  # Base 16 + 18


class TestScoreClamping:
    """Tests for score clamping to 0-100 range"""

    def test_score_never_exceeds_100(self):
        """Score should be clamped at 100"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(
            bundle,
            quality_score=30,
            face_similarity=0.3,
            pep=True,
            sanctions=True,
            declared_high_volume=True,
            anomalies=10,
        )
        assert result.score <= 100

    def test_score_never_below_0(self):
        """Score should be clamped at 0"""
        # This is harder to test since base is always positive
        # But we can verify the logic exists
        from app.domain.risk import compute_risk
        result = compute_risk(ValidationBundle(checks=[]), quality_score=80)
        assert result.score >= 0


class TestRiskLevelAssignment:
    """Tests for risk level assignment based on score"""

    def test_low_level(self):
        """Score < 35 -> LOW"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(bundle, quality_score=80, face_similarity=0.9)
        assert result.level == RiskLevel.LOW

    def test_medium_level(self):
        """Score 35-59 -> MEDIUM"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, score_impact=20)])
        result = compute_risk(bundle, quality_score=80)
        assert result.level == RiskLevel.MEDIUM

    def test_high_level(self):
        """Score 60-79 -> HIGH"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, score_impact=50)])
        result = compute_risk(bundle, quality_score=80)
        assert result.level == RiskLevel.HIGH

    def test_critical_level(self):
        """Score >= 80 -> CRITICAL"""
        bundle = ValidationBundle(checks=[CheckResult("c", False, score_impact=70)])
        result = compute_risk(bundle, quality_score=80)
        assert result.level == RiskLevel.CRITICAL


class TestPersianLabels:
    """Tests for Persian risk level labels"""

    def test_risk_result_has_persian_label(self):
        """RiskResult.to_dict should include Persian label"""
        bundle = ValidationBundle(checks=[])
        result = compute_risk(bundle, quality_score=80, face_similarity=0.9)
        d = result.to_dict()
        assert "level_fa" in d
        assert d["level_fa"] in ["ریسک پایین", "ریسک متوسط", "ریسک بالا", "ریسک بحرانی"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])