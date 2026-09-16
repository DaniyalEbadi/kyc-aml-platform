from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256


@dataclass
class FaceResult:
    similarity: float
    quality_score: float
    confidence: float
    decision: str
    reasons: list[str]
    provider: str
    is_simulated: bool
    liveness_placeholder: str = "معماری تشخیص زنده بودن آماده اتصال است و در این نسخه اجرا نمی‌شود."

    def to_dict(self) -> dict:
        return self.__dict__


class VisionProvider(ABC):
    @abstractmethod
    def compare(self, id_bytes: bytes, selfie_bytes: bytes) -> FaceResult:
        ...


class MockVisionProvider(VisionProvider):
    def compare(self, id_bytes: bytes, selfie_bytes: bytes) -> FaceResult:
        a = int(sha256(id_bytes[:2048] or b"id").hexdigest()[:6], 16)
        b = int(sha256(selfie_bytes[:2048] or b"sf").hexdigest()[:6], 16)
        delta = abs(a - b) % 40
        similarity = max(0.35, 0.96 - delta / 120)
        quality = 0.78 + (len(selfie_bytes) % 17) / 100
        decision = "match" if similarity >= 0.62 else "mismatch"
        reasons = ["شباهت بر اساس مقایسه تعبیه شبیه‌سازی‌شده محاسبه شد."]
        if decision == "mismatch":
            reasons.append("امتیاز شباهت کمتر از آستانه پیکربندی‌شده است.")
        return FaceResult(similarity, min(quality, 0.99), 0.72, decision, reasons, "mock", True)


def get_vision_provider(_: str) -> VisionProvider:
    return MockVisionProvider()
