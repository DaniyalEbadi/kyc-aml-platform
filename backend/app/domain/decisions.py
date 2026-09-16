from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import DecisionCode, RiskLevel
from app.domain.rules import ValidationBundle


@dataclass
class DecisionOutcome:
    code: DecisionCode
    reason: str
    auto: bool

    def to_dict(self) -> dict:
        return {"code": self.code.value, "reason": self.reason, "auto": self.auto}


def decide(
    bundle: ValidationBundle,
    risk_level: RiskLevel,
    pep_match: bool,
    sanctions_match: bool,
) -> DecisionOutcome:
    """
    Deterministic decision boundary. The LLM must never replace this function.
    Inherited from the original agent: escalate / resubmit / approve.
    Rejection is only produced by a human reviewer, not auto-rules,
    except sanctions which force specialist review (not silent reject).
    """
    if sanctions_match or pep_match or risk_level == RiskLevel.CRITICAL:
        return DecisionOutcome(
            DecisionCode.UNDER_REVIEW,
            "تطبیق تحریم/اشخاص سیاسی یا ریسک بحرانی؛ ارجاع اجباری به بررسی انسانی.",
            auto=True,
        )
    if risk_level == RiskLevel.HIGH or bundle.requires_escalation:
        return DecisionOutcome(
            DecisionCode.UNDER_REVIEW,
            "ریسک بالا یا ناهم‌خوانی هویتی؛ سامانه اجازه تأیید خودکار ندارد.",
            auto=True,
        )
    if bundle.requires_resubmission:
        return DecisionOutcome(
            DecisionCode.RESUBMISSION_REQUESTED,
            "نقص یا انقضای مدرک؛ طبق سیاست باید ارسال مجدد شود نه رد خودکار.",
            auto=True,
        )
    return DecisionOutcome(
        DecisionCode.APPROVED,
        "تمام بررسی‌های قطعی پاس شده و سطح ریسک اجازه تأیید خودکار می‌دهد.",
        auto=True,
    )
