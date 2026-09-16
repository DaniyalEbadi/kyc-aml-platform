from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        ...


class MockLLMProvider(LLMProvider):
    def generate(self, system_prompt: str, user_message: str) -> str:
        decision = None
        for line in user_message.splitlines():
            if line.startswith("Decision computed by policy engine:"):
                decision = line.split(":", 1)[1].strip()
                break
        if decision == "under_review_by_specialist":
            return (
                "بر اساس قواعد قطعی سامانه، این پرونده خارج از محدوده تأیید خودکار است و "
                "برای بررسی متخصص انطباق ارجاع شده است. تصمیم نهایی توسط مدل زبانی گرفته نشده است."
            )
        if decision == "resubmission_requested":
            return (
                "بررسی قطعی مدارک نشان می‌دهد مدرک باید دوباره ارسال شود. "
                "درخواست رد نشده است؛ پس از بارگذاری مدرک معتبر، پردازش ادامه می‌یابد."
            )
        if decision == "approved":
            return "تمام کنترل‌های قطعی و سیاست فعال پاس شده‌اند. پیام تأیید برای مشتری تهیه شد."
        if "اطلاعات کافی" in user_message:
            return "اطلاعات کافی برای پاسخ قطعی وجود ندارد."
        return (
            "پاسخ بر اساس خروجی ابزارها و بندهای بازیابی‌شده سیاست تهیه شد. "
            "هیچ قاعده سیاستی جعل نشده است."
        )


def get_llm_provider(_: str) -> LLMProvider:
    return MockLLMProvider()
