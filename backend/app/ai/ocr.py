from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional

from PIL import Image, ImageFilter, ImageOps, ImageStat


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


# ---------------------------------------------------------------------------
# Image preprocessing for better OCR accuracy
# ---------------------------------------------------------------------------

def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    w, h = img.size
    if min(w, h) < 1000:
        scale = 1000 / min(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    threshold = 140
    img = img.point(lambda p: 255 if p > threshold else 0)
    return img


def _preprocess_color(img: Image.Image) -> Image.Image:
    w, h = img.size
    if min(w, h) < 1000:
        scale = 1000 / min(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.SHARPEN)
    return img


# ---------------------------------------------------------------------------
# Persian national card field parser
# ---------------------------------------------------------------------------

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

_NATIONAL_ID_RE = re.compile(r"[0-9۰-۹]{10}")
_DATE_RE = re.compile(r"[0-9۰-۹]{4}[/\-][0-9۰-۹]{1,2}[/\-][0-9۰-۹]{1,2}")
_BIRTH_CERT_RE = re.compile(r"[0-9۰-۹]{1,10}")

_LABEL_MAP = {
    "نام": "first_name",
    "نام و نام خانوادگی": "full_name",
    "نام خانوادگی": "last_name",
    "شماره ملی": "national_id",
    "شماره شناسنامه": "birth_certificate_number",
    "کد ملی": "national_id",
    "تاریخ تولد": "birth_date",
    "تولد": "birth_date",
    "جنسیت": "gender",
    "نام پدر": "father_name",
    "تاریخ صدور": "issue_date",
    "تاریخ انقضا": "expiry_date",
    "محل صدور": "issue_place",
    "شماره گذرنامه": "passport_number",
}

_GENDER_MAP = {
    "مرد": "male",
    "مردانه": "male",
    "مذکر": "male",
    "زن": "female",
    "زنانه": "female",
    "مونث": "female",
}

_MONTH_NAMES = {
    "ژانویه": 1, "فوریه": 2, "مارس": 3, "آوریل": 4,
    "مه": 5, "ژوئن": 6, "ژوئیه": 7, "اوت": 8,
    "سپتامبر": 9, "اکتبر": 10, "نوامبر": 11, "دسامبر": 12,
}


def _to_latin_digits(s: str) -> str:
    return s.translate(_PERSIAN_DIGITS)


def _parse_national_card(raw_text: str, lines: list[str]) -> list[Extracted]:
    fields: list[Extracted] = []
    latin = _to_latin_digits(raw_text)
    lower_lines = [l.strip() for l in lines if l.strip()]

    name_candidates = []
    for line in lower_lines:
        cleaned = re.sub(r"[^\w\s]", "", line).strip()
        if not cleaned:
            continue
        if any(kw in cleaned for kw in _LABEL_MAP):
            continue
        if re.search(r"[0-9]", cleaned) and len(cleaned) < 20:
            continue
        if any(ch in cleaned for ch in ["@","#","$","%","&","*","/","\\"]):
            continue
        if 2 <= len(cleaned) <= 40 and not re.fullmatch(r"[\s]+", cleaned):
            name_candidates.append(cleaned)

    national_id_match = _NATIONAL_ID_RE.search(latin)
    if national_id_match:
        nid = national_id_match.group()
        if len(nid) == 10:
            fields.append(Extracted("national_id", "شماره ملی", nid, 0.92))
    else:
        for line in lower_lines:
            nums = re.findall(r"[0-9]+", _to_latin_digits(line))
            for n in nums:
                if len(n) == 10 and n[0] in "0123456789":
                    fields.append(Extracted("national_id", "شماره ملی", n, 0.85))
                    break
            if any(f.field_name == "national_id" for f in fields):
                break

    date_matches = _DATE_RE.findall(latin)
    date_values = [_to_latin_digits(d) for d in date_matches]
    persian_dates = _DATE_RE.findall(raw_text)

    if date_values:
        if len(date_values) >= 3:
            fields.append(Extracted("birth_date", "تاریخ تولد", date_values[0], 0.88))
            fields.append(Extracted("issue_date", "تاریخ صدور", date_values[1], 0.85))
            fields.append(Extracted("expiry_date", "تاریخ انقضا", date_values[2], 0.82))
        elif len(date_values) == 2:
            fields.append(Extracted("birth_date", "تاریخ تولد", date_values[0], 0.85))
            fields.append(Extracted("issue_date", "تاریخ صدور", date_values[1], 0.80))
        elif len(date_values) == 1:
            fields.append(Extracted("birth_date", "تاریخ تولد", date_values[0], 0.80))

    for line in lower_lines:
        if "جنسیت" in line or "جنسيت" in line:
            for persian, english in _GENDER_MAP.items():
                if persian in line:
                    fields.append(Extracted("gender", "جنسیت", english, 0.88))
                    break
            if not any(f.field_name == "gender" for f in fields):
                if "مرد" in line or "مذکر" in line:
                    fields.append(Extracted("gender", "جنسیت", "male", 0.80))
                elif "زن" in line or "مونث" in line:
                    fields.append(Extracted("gender", "جنسیت", "female", 0.80))

    if not any(f.field_name == "gender" for f in fields):
        for line in lower_lines:
            for persian, english in _GENDER_MAP.items():
                if persian in line:
                    fields.append(Extracted("gender", "جنسیت", english, 0.70))
                    break
            if any(f.field_name == "gender" for f in fields):
                break

    for line in lower_lines:
        for label_persian, field_name in _LABEL_MAP.items():
            if label_persian in line:
                value_part = line.split(label_persian)[-1].strip()
                value_part = re.sub(r"[:\-=]+", "", value_part).strip()
                if value_part and len(value_part) > 1:
                    already = any(f.field_name == field_name for f in fields)
                    if not already:
                        conf = 0.87 if field_name in ("first_name", "last_name") else 0.80
                        fields.append(Extracted(field_name, label_persian, value_part, conf))

    for line in lower_lines:
        if "نام پدر" in line or "نام padre" in line.lower():
            value = line.split("نام پدر")[-1].strip()
            value = re.sub(r"[:\-=]+", "", value).strip()
            if value and len(value) > 1 and not any(f.field_name == "father_name" for f in fields):
                fields.append(Extracted("father_name", "نام پدر", value, 0.80))

    if not any(f.field_name == "first_name" for f in fields):
        non_label_lines = []
        for line in lower_lines:
            cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", "", line).strip()
            if not cleaned or re.search(r"[0-9]{3,}", cleaned):
                continue
            if any(kw in cleaned for kw in _LABEL_MAP.values()):
                continue
            if any(kw in cleaned for kw in _LABEL_MAP.keys()):
                continue
            if 2 <= len(cleaned) <= 30:
                non_label_lines.append(cleaned)

        if len(non_label_lines) >= 2:
            fields.append(Extracted("first_name", "نام", non_label_lines[0], 0.72))
            fields.append(Extracted("last_name", "نام خانوادگی", non_label_lines[1], 0.70))
        elif len(non_label_lines) == 1:
            parts = non_label_lines[0].split()
            if len(parts) >= 2:
                fields.append(Extracted("first_name", "نام", parts[0], 0.68))
                fields.append(Extracted("last_name", "نام خانوادگی", " ".join(parts[1:]), 0.65))

    for line in lower_lines:
        if "محل صدور" in line:
            value = line.split("محل صدور")[-1].strip()
            value = re.sub(r"[:\-=]+", "", value).strip()
            if value and not any(f.field_name == "issue_place" for f in fields):
                fields.append(Extracted("issue_place", "محل صدور", value, 0.75))

    return fields


def _parse_passport(raw_text: str, lines: list[str]) -> list[Extracted]:
    fields: list[Extracted] = []
    latin = _to_latin_digits(raw_text)
    mrz_lines = [l for l in lines if l.startswith("P<") or (len(l) > 30 and re.match(r"^[A-Z0-9<]", l))]

    if mrz_lines:
        mrz_text = "".join(mrz_lines)
        name_match = re.search(r"P<([A-Z]+)<<?([A-Z<]+)", mrz_text)
        if name_match:
            surname = name_match.group(1).replace("<", " ")
            given = name_match.group(2).replace("<", " ").strip()
            fields.append(Extracted("first_name", "نام", given, 0.90))
            fields.append(Extracted("last_name", "نام خانوادگی", surname, 0.88))

        passport_match = re.search(r"[A-Z]{2}[0-9]{7}", mrz_text)
        if passport_match:
            fields.append(Extracted("passport_number", "شماره گذرنامه", passport_match.group(), 0.92))

        date_matches = re.findall(r"([0-9]{6})[0-9]", mrz_text)
        if len(date_matches) >= 2:
            fields.append(Extracted("birth_date", "تاریخ تولد", _format_mrz_date(date_matches[0]), 0.88))
            fields.append(Extracted("expiry_date", "تاریخ انقضا", _format_mrz_date(date_matches[1]), 0.85))

    if not any(f.field_name == "national_id" for f in fields):
        nid_match = _NATIONAL_ID_RE.search(latin)
        if nid_match:
            fields.append(Extracted("national_id", "شماره ملی", nid_match.group(), 0.80))

    return fields


def _format_mrz_date(d: str) -> str:
    if len(d) == 6:
        yy, mm, dd = d[:2], d[2:4], d[4:6]
        year = 2000 + int(yy) if int(yy) < 50 else 1900 + int(yy)
        return f"{year}-{mm}-{dd}"
    return d


def _parse_driver_license(raw_text: str, lines: list[str]) -> list[Extracted]:
    fields: list[Extracted] = []
    latin = _to_latin_digits(raw_text)

    nid_match = _NATIONAL_ID_RE.search(latin)
    if nid_match and len(nid_match.group()) == 10:
        fields.append(Extracted("national_id", "شماره ملی", nid_match.group(), 0.88))

    date_matches = _DATE_RE.findall(latin)
    if date_matches:
        fields.append(Extracted("birth_date", "تاریخ تولد", date_matches[0], 0.82))
        if len(date_matches) >= 2:
            fields.append(Extracted("expiry_date", "تاریخ انقضا", date_matches[1], 0.78))

    for line in lines:
        for label_persian, field_name in _LABEL_MAP.items():
            if label_persian in line:
                value = line.split(label_persian)[-1].strip()
                value = re.sub(r"[:\-=]+", "", value).strip()
                if value and len(value) > 1 and not any(f.field_name == field_name for f in fields):
                    fields.append(Extracted(field_name, label_persian, value, 0.75))

    return fields


_PARSERS = {
    "national_id": _parse_national_card,
    "passport": _parse_passport,
    "driver_license": _parse_driver_license,
    "proof_of_address": _parse_national_card,
    "selfie": _parse_national_card,
    "business": _parse_national_card,
    "residence": _parse_national_card,
}


# ---------------------------------------------------------------------------
# EasyOCR-based provider (real OCR)
# ---------------------------------------------------------------------------

class EasyOCRProvider(OCRProvider):
    _reader = None

    @classmethod
    def _get_reader(cls):
        if cls._reader is None:
            try:
                import easyocr
                cls._reader = easyocr.Reader(
                    ["fa", "en"],
                    gpu=False,
                    verbose=False,
                    model_storage_directory=None,
                )
            except Exception:
                return None
        return cls._reader

    def extract(self, data: bytes, filename: str, hint_type: str, context: dict) -> OCRResult:
        reader = self._get_reader()
        if reader is None:
            return MockOCRProvider().extract(data, filename, hint_type, context)

        try:
            image = Image.open(BytesIO(data))
            processed = _preprocess_for_ocr(image)
            import numpy as np
            img_array = np.array(processed)

            results = reader.readtext(img_array, detail=1, paragraph=False)

            raw_lines = []
            all_text_parts = []
            for bbox, text, conf in results:
                raw_lines.append(text)
                all_text_parts.append(text)

            raw_text = "\n".join(raw_lines)

            image_color = _preprocess_color(Image.open(BytesIO(data)).convert("RGB"))
            img_color_array = np.array(image_color)
            results_color = reader.readtext(img_color_array, detail=1, paragraph=False)
            for bbox, text, conf in results_color:
                if text not in raw_lines:
                    raw_lines.append(text)
                    raw_text += "\n" + text

            parser = _PARSERS.get(hint_type, _parse_national_card)
            fields = parser(raw_text, raw_lines)

            if not fields:
                fields = MockOCRProvider().extract(data, filename, hint_type, context).fields
                is_simulated = True
            else:
                is_simulated = False

            avg_conf = sum(f.confidence for f in fields) / max(len(fields), 1)

            return OCRResult(
                document_type=hint_type,
                fields=fields,
                raw_text=raw_text,
                provider="easyocr",
                is_simulated=is_simulated,
            )
        except Exception as exc:
            result = MockOCRProvider().extract(data, filename, hint_type, context)
            result.raw_text = f"OCR_ERROR: {exc}"
            return result


# ---------------------------------------------------------------------------
# Fallback mock provider (no real OCR)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Document classifier + processor
# ---------------------------------------------------------------------------

class DocumentProcessor:
    def __init__(self, ocr: OCRProvider):
        self.ocr = ocr

    def classify(self, hint_type: str, filename: str) -> str:
        name = filename.lower()
        mapping = {
            "passport": "passport",
            "meli": "national_id",
            "national": "national_id",
            "کارت ملی": "national_id",
            "کارت_ملی": "national_id",
            "license": "driver_license",
            "گواهینامه": "driver_license",
            "address": "proof_of_address",
            "selfie": "selfie",
            "سلفی": "selfie",
        }
        for key, value in mapping.items():
            if key in name:
                return value
        return hint_type or "national_id"

    def extract(self, data: bytes, filename: str, hint_type: str, context: dict) -> OCRResult:
        classified = self.classify(hint_type, filename)
        return self.ocr.extract(data, filename, classified, context)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_ocr_provider(name: str) -> OCRProvider:
    if name == "easyocr":
        return EasyOCRProvider()
    return MockOCRProvider()
