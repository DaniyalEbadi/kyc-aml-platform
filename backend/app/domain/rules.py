from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from rapidfuzz import fuzz


@dataclass
class CheckResult:
    code: str
    passed: bool
    escalate: bool = False
    resubmit: bool = False
    message: str = ""
    score_impact: int = 0

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "passed": self.passed,
            "escalate": self.escalate,
            "resubmit": self.resubmit,
            "message": self.message,
            "score_impact": self.score_impact,
        }


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def names_match(name_a: str, name_b: str) -> bool:
    """Token-overlap heuristic from the original agent, plus fuzzy ratio."""
    def tokens(name: str) -> set[str]:
        cleaned = name.lower().replace(".", "").replace(",", "").replace("‌", " ")
        return {t for t in cleaned.split() if len(t) > 1}

    a, b = tokens(name_a or ""), tokens(name_b or "")
    if not a or not b:
        return False
    overlap = a & b
    smaller = min(len(a), len(b))
    token_ok = len(overlap) >= max(1, smaller - 1)
    ratio = fuzz.token_set_ratio(name_a, name_b)
    return token_ok or ratio >= 82


def validate_iranian_national_id(nid: str | None) -> bool:
    if not nid or not nid.isdigit() or len(nid) != 10:
        return False
    if len(set(nid)) == 1:
        return False
    check = int(nid[9])
    total = sum(int(nid[i]) * (10 - i) for i in range(9))
    rem = total % 11
    return (rem < 2 and check == rem) or (rem >= 2 and check == 11 - rem)


def validate_identity_expiry(expiry_value: str | None, today: date | None = None) -> CheckResult:
    today = today or date.today()
    expiry = parse_date(expiry_value)
    if expiry is None:
        return CheckResult("identity_expiry", False, resubmit=True, score_impact=18, message="تاریخ انقضای مدرک هویتی نامعتبر است.")
    if expiry < today:
        return CheckResult(
            "identity_expiry",
            False,
            resubmit=True,
            score_impact=25,
            message=f"مدرک هویتی در تاریخ {expiry.isoformat()} منقضی شده است.",
        )
    return CheckResult("identity_expiry", True, message="مدرک هویتی منقضی نشده است.")


def validate_name_consistency(document_name: str, application_name: str) -> CheckResult:
    if names_match(document_name, application_name):
        return CheckResult("name_match", True, message="نام مدرک با درخواست هم‌خوان است.")
    return CheckResult(
        "name_match",
        False,
        escalate=True,
        score_impact=30,
        message=f"نام روی مدرک («{document_name}») با نام درخواست («{application_name}») هم‌خوان نیست.",
    )


def validate_proof_of_address_age(document_date: str | None, today: date | None = None, limit_days: int = 90) -> CheckResult:
    today = today or date.today()
    parsed = parse_date(document_date)
    if parsed is None:
        return CheckResult("address_age", False, resubmit=True, score_impact=12, message="تاریخ مدرک نشانی نامعتبر است.")
    age_days = (today - parsed).days
    if age_days > limit_days:
        return CheckResult(
            "address_age",
            False,
            resubmit=True,
            score_impact=16,
            message=f"مدرک نشانی {age_days} روزه است (حد مجاز {limit_days} روز).",
        )
    return CheckResult("address_age", True, message="مدرک نشانی در بازه مجاز است.")


def validate_national_id_field(nid: str | None) -> CheckResult:
    if not nid:
        return CheckResult("national_id", True, message="شماره ملی ارائه نشده؛ در صورت کارت ملی الزامی است.")
    if validate_iranian_national_id(nid):
        return CheckResult("national_id", True, message="الگوریتم شماره ملی معتبر است.")
    return CheckResult("national_id", False, escalate=True, score_impact=22, message="شماره ملی از نظر الگوریتم کنترل نامعتبر است.")


@dataclass
class ValidationBundle:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_issues(self) -> list[str]:
        return [c.message for c in self.checks if not c.passed]

    @property
    def requires_escalation(self) -> bool:
        return any(c.escalate for c in self.checks)

    @property
    def requires_resubmission(self) -> bool:
        return any(c.resubmit for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "checks": [c.to_dict() for c in self.checks],
            "all_issues": self.all_issues,
            "requires_escalation": self.requires_escalation,
            "requires_resubmission": self.requires_resubmission,
        }


def validate_application_payload(payload: dict, today: date | None = None) -> ValidationBundle:
    """Canonical deterministic checks. LLM never calls this internally."""
    bundle = ValidationBundle()
    identity = payload.get("identity_document") or {}
    address = payload.get("proof_of_address") or {}
    customer_name = payload.get("customer_name") or ""
    bundle.checks.append(validate_identity_expiry(identity.get("expiry_date"), today))
    if identity.get("name_on_document"):
        bundle.checks.append(validate_name_consistency(identity["name_on_document"], customer_name))
    if address:
        bundle.checks.append(validate_proof_of_address_age(address.get("document_date"), today))
    if payload.get("national_id"):
        bundle.checks.append(validate_national_id_field(payload.get("national_id")))
    quality = payload.get("quality") or {}
    if quality.get("overall", 100) < 45:
        bundle.checks.append(
            CheckResult("document_quality", False, resubmit=True, score_impact=20, message="کیفیت تصویر مدرک برای استخراج قابل اعتماد نیست.")
        )
    else:
        bundle.checks.append(CheckResult("document_quality", True, message="کیفیت مدرک در آستانه قابل قبول است."))
    face = payload.get("face") or {}
    if face.get("similarity") is not None and face["similarity"] < 0.62:
        bundle.checks.append(
            CheckResult("face_match", False, escalate=True, score_impact=28, message="شباهت چهره پایین‌تر از آستانه سیاست است.")
        )
    return bundle
