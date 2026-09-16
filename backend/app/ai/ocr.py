from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Extracted:
    field_name: str
    field_label: str
    value: str
    confidence: float


@dataclass
class OCRResult:
    document_type: str
    fields: list[Extracted]
    raw_text: str
    provider: str
    is_simulated: bool


class OCRProvider(ABC):
    @abstractmethod
    def extract(self, data: bytes, filename: str, hint_type: str, context: dict) -> OCRResult:
        ...


class MockOCRProvider(OCRProvider):
    def extract(self, data: bytes, filename: str, hint_type: str, context: dict) -> OCRResult:
        first = context.get("first_name", "نامشخص")
        last = context.get("last_name", "نامشخص")
        nid = context.get("national_id") or "0012345678"
        fields = [
            Extracted("first_name", "نام", first, 0.91),
            Extracted("last_name", "نام خانوادگی", last, 0.9),
            Extracted("national_id", "شماره ملی", nid, 0.88),
            Extracted("birth_date", "تاریخ تولد", context.get("birth_date") or "1990-04-12", 0.81),
            Extracted("issue_date", "تاریخ صدور", "2020-01-15", 0.77),
            Extracted("expiry_date", "تاریخ انقضا", context.get("expiry_date") or "2030-01-14", 0.84),
            Extracted("gender", "جنسیت", context.get("gender") or "نامشخص", 0.7),
            Extracted("nationality", "ملیت", context.get("nationality") or "ایران", 0.86),
            Extracted("address", "آدرس", context.get("address") or "تهران", 0.62),
            Extracted("passport_number", "شماره گذرنامه", context.get("passport_number") or "", 0.5),
        ]
        if "fail" in filename.lower():
            for f in fields:
                f.confidence *= 0.4
        return OCRResult(hint_type, fields, "MOCK_OCR", "mock", True)


class DocumentProcessor:
    def __init__(self, ocr: OCRProvider):
        self.ocr = ocr

    def classify(self, hint_type: str, filename: str) -> str:
        name = filename.lower()
        mapping = {
            "passport": "passport",
            "meli": "national_id",
            "national": "national_id",
            "license": "driver_license",
            "address": "proof_of_address",
            "selfie": "selfie",
        }
        for key, value in mapping.items():
            if key in name:
                return value
        return hint_type or "national_id"

    def extract(self, data: bytes, filename: str, hint_type: str, context: dict) -> OCRResult:
        classified = self.classify(hint_type, filename)
        return self.ocr.extract(data, filename, classified, context)


def get_ocr_provider(name: str) -> OCRProvider:
    return MockOCRProvider()
