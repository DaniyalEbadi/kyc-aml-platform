from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from rapidfuzz import fuzz


@dataclass
class Hit:
    kind: str
    matched: bool
    score: float
    list_name: str
    matched_name: str | None
    is_simulated: bool
    note: str


class ScreeningProvider(ABC):
    @abstractmethod
    def screen(self, full_name: str, national_id: str | None) -> list[Hit]:
        ...


_SANCTIONS = ["جان اسمیت تحریم‌شده", "شرکت صوری البرز"]
_PEP = ["علی سیاسی‌زاده", "مریم مقام‌دار"]


class MockScreeningProvider(ScreeningProvider):
    def screen(self, full_name: str, national_id: str | None) -> list[Hit]:
        note = "نتایج غربالگری شبیه‌سازی‌شده‌اند و داده واقعی فهرست تحریم نیستند."
        san_score = max((fuzz.token_set_ratio(full_name, n) for n in _SANCTIONS), default=0)
        pep_score = max((fuzz.token_set_ratio(full_name, n) for n in _PEP), default=0)
        forced = "تحریم" in (full_name or "") or (national_id or "").endswith("0000")
        forced_pep = "سیاسی" in (full_name or "") or (national_id or "").endswith("1111")
        return [
            Hit("sanctions", forced or san_score >= 90, (100.0 if forced else float(san_score)), "لیست آزمایشی تحریم", full_name if forced else None, True, note),
            Hit("pep", forced_pep or pep_score >= 90, (100.0 if forced_pep else float(pep_score)), "فهرست آزمایشی PEP", full_name if forced_pep else None, True, note),
            Hit("adverse_media", False, 8.0, "رسانه آزمایشی", None, True, note),
            Hit("watchlist", False, 5.0, "فهرست مراقبت آزمایشی", None, True, note),
        ]


def get_screening_provider(_: str) -> ScreeningProvider:
    return MockScreeningProvider()
