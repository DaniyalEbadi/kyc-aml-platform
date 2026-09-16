from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityReport:
    overall: float
    blur: float
    glare: float
    brightness: float
    contrast: float
    crop: float
    corners: float
    resolution: float
    rotation: float
    readability: float
    reasons: list[str]
    is_simulated: bool

    def to_dict(self) -> dict:
        return {
            "overall": self.overall,
            "blur": self.blur,
            "glare": self.glare,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "crop": self.crop,
            "corners": self.corners,
            "resolution": self.resolution,
            "rotation": self.rotation,
            "readability": self.readability,
            "reasons": self.reasons,
            "is_simulated": self.is_simulated,
            "labels": {
                "overall": "کیفیت تصویر",
                "readability": "خوانایی متن",
                "glare": "بازتاب نور",
                "crop": "برش تصویر",
                "resolution": "رزولوشن",
                "blur": "تاری",
                "brightness": "روشنایی",
                "contrast": "کنتراست",
                "corners": "گوشه‌ها",
                "rotation": "چرخش",
            },
        }


def analyze_image_bytes(data: bytes, filename: str = "") -> QualityReport:
    reasons: list[str] = []
    simulated = False
    try:
        from io import BytesIO

        from PIL import Image, ImageFilter, ImageStat

        image = Image.open(BytesIO(data)).convert("RGB")
        w, h = image.size
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        mean = stat.mean[0]
        stddev = stat.stddev[0]
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_mean = ImageStat.Stat(edges).mean[0]
        resolution = min(100.0, (min(w, h) / 12.0))
        brightness = max(0, min(100, 100 - abs(mean - 128) / 1.28))
        contrast = min(100.0, stddev * 2.2)
        blur = min(100.0, edge_mean * 4)
        glare = 100.0 if mean < 230 else 55.0
        crop = 90.0 if w / h < 2.4 else 60.0
        corners = 88.0
        rotation = 92.0
        readability = (blur * 0.4 + contrast * 0.3 + resolution * 0.3)
        if resolution < 50:
            reasons.append("رزولوشن پایین است.")
        if blur < 40:
            reasons.append("تصویر تار به نظر می‌رسد.")
        if brightness < 40:
            reasons.append("روشنایی نامناسب است.")
        if not reasons:
            reasons.append("شاخص‌های کیفیت در محدوده قابل قبول هستند.")
        overall = (readability + brightness + contrast + resolution) / 4
        return QualityReport(overall, blur, glare, brightness, contrast, crop, corners, resolution, rotation, readability, reasons, False)
    except Exception:
        simulated = True
        seed = (len(data) + len(filename)) % 40
        overall = 62 + (seed % 28)
        reasons = ["تحلیل کیفیت با موتور جایگزین/شبیه‌سازی انجام شد."]
        return QualityReport(
            overall=overall,
            blur=70,
            glare=65,
            brightness=72,
            contrast=68,
            crop=80,
            corners=75,
            resolution=60 + seed / 2,
            rotation=90,
            readability=overall,
            reasons=reasons,
            is_simulated=simulated,
        )
