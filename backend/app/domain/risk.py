from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import RiskLevel
from app.domain.rules import ValidationBundle


@dataclass
class Factor:
    code: str
    label: str
    weight: int
    triggered: bool
    detail: str


@dataclass
class RiskResult:
    score: int
    level: RiskLevel
    factors: list[Factor] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level.value,
            "level_fa": {
                RiskLevel.LOW: "ریسک پایین",
                RiskLevel.MEDIUM: "ریسک متوسط",
                RiskLevel.HIGH: "ریسک بالا",
                RiskLevel.CRITICAL: "ریسک بحرانی",
            }[self.level],
            "factors": [f.__dict__ for f in self.factors],
        }


def _level(score: int) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 35:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def compute_risk(
    bundle: ValidationBundle,
    *,
    quality_score: float = 80,
    face_similarity: float | None = None,
    pep: bool = False,
    sanctions: bool = False,
    jurisdiction_risk: int = 10,
    anomalies: int = 0,
    declared_high_volume: bool = False,
) -> RiskResult:
    factors: list[Factor] = []
    score = 8 + jurisdiction_risk

    for check in bundle.checks:
        if not check.passed:
            factors.append(
                Factor(check.code, check.message, check.score_impact, True, check.message)
            )
            score += check.score_impact

    if quality_score < 55:
        factors.append(Factor("quality", "کیفیت مدرک", 14, True, f"امتیاز کیفیت {quality_score:.0f}"))
        score += 14
    else:
        factors.append(Factor("quality", "کیفیت مدرک", 0, False, "کیفیت قابل قبول"))

    if face_similarity is not None:
        if face_similarity < 0.62:
            factors.append(Factor("face", "تطبیق چهره", 22, True, f"شباهت {face_similarity:.2f}"))
            score += 22
        else:
            factors.append(Factor("face", "تطبیق چهره", 0, False, f"شباهت {face_similarity:.2f}"))

    if pep:
        factors.append(Factor("pep", "اشخاص سیاسی", 35, True, "تطبیق PEP (داده‌ شبیه‌سازی‌شده در حالت توسعه)"))
        score += 35
    if sanctions:
        factors.append(Factor("sanctions", "تحریم‌ها", 50, True, "تطبیق فهرست تحریم (داده‌ شبیه‌سازی‌شده در حالت توسعه)"))
        score += 50
    if declared_high_volume:
        factors.append(Factor("volume", "حجم تراکنش مورد انتظار", 8, True, "حجم اعلام‌شده بالا"))
        score += 8
    if anomalies:
        factors.append(Factor("anomaly", "ناهنجاری درخواست", 6 * anomalies, True, f"{anomalies} شاخص مشکوک"))
        score += 6 * anomalies

    score = max(0, min(100, score))
    return RiskResult(score=score, level=_level(score), factors=factors)
