from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import bad_request


class LocalStorage:
    def __init__(self) -> None:
        self.root = Path(settings.storage_local_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, upload: UploadFile, data: bytes) -> str:
        if upload.content_type not in settings.allowed_types:
            raise bad_request("نوع فایل مجاز نیست.")
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise bad_request("حجم فایل بیش از حد مجاز است.")
        ext = Path(upload.filename or "file.bin").suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".pdf"}:
            raise bad_request("پسوند فایل مجاز نیست.")
        key = f"{uuid4().hex}{ext}"
        path = self.root / key
        path.write_bytes(data)
        return key

    def read(self, key: str) -> bytes:
        if ".." in key or "/" in key or "\\" in key:
            raise bad_request("کلید ذخیره‌سازی نامعتبر است.")
        path = self.root / key
        if not path.exists():
            raise bad_request("فایل یافت نشد.")
        return path.read_bytes()


storage = LocalStorage()


def virus_scan_hook(data: bytes) -> None:
    """Integration point for ClamAV / similar. Demo: reject EICAR marker."""
    if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in data:
        raise bad_request("فایل توسط بررسی امنیتی مسدود شد.")


def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:180]
