from __future__ import annotations

from enum import StrEnum


class RoleName(StrEnum):
    APPLICANT = "applicant"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    ADMIN = "admin"
    AUDITOR = "auditor"


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    NEEDS_RESUBMISSION = "needs_resubmission"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class DocumentType(StrEnum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVER_LICENSE = "driver_license"
    RESIDENCE = "residence"
    PROOF_OF_ADDRESS = "proof_of_address"
    BUSINESS = "business"
    SELFIE = "selfie"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REJECTED = "rejected"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    WAITING_CUSTOMER = "waiting_customer"
    ESCALATED = "escalated"
    CLOSED = "closed"


class CasePriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionCode(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RESUBMISSION_REQUESTED = "resubmission_requested"
    UNDER_REVIEW = "under_review_by_specialist"


class ScreeningKind(StrEnum):
    SANCTIONS = "sanctions"
    PEP = "pep"
    ADVERSE_MEDIA = "adverse_media"
    WATCHLIST = "watchlist"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OnboardingStep(StrEnum):
    PERSONAL = "personal"
    CONTACT = "contact"
    ID_UPLOAD = "id_upload"
    QUALITY = "quality"
    EXTRACTION = "extraction"
    CONFIRM_FIELDS = "confirm_fields"
    SELFIE = "selfie"
    ADDITIONAL = "additional"
    REVIEW = "review"
    SUBMIT = "submit"


RISK_LEVEL_FA = {
    RiskLevel.LOW: "ریسک پایین",
    RiskLevel.MEDIUM: "ریسک متوسط",
    RiskLevel.HIGH: "ریسک بالا",
    RiskLevel.CRITICAL: "ریسک بحرانی",
}

STATUS_FA = {
    ApplicationStatus.DRAFT: "پیش‌نویس",
    ApplicationStatus.SUBMITTED: "ارسال‌شده",
    ApplicationStatus.PROCESSING: "در حال پردازش",
    ApplicationStatus.NEEDS_RESUBMISSION: "نیاز به ارسال مجدد",
    ApplicationStatus.IN_REVIEW: "در انتظار بررسی",
    ApplicationStatus.APPROVED: "تأیید شده",
    ApplicationStatus.REJECTED: "رد شده",
    ApplicationStatus.ESCALATED: "ارجاع‌شده",
}

DOCUMENT_TYPE_FA = {
    DocumentType.PASSPORT: "گذرنامه",
    DocumentType.NATIONAL_ID: "کارت ملی",
    DocumentType.DRIVER_LICENSE: "گواهینامه",
    DocumentType.RESIDENCE: "مدرک اقامت",
    DocumentType.PROOF_OF_ADDRESS: "مدرک نشانی",
    DocumentType.BUSINESS: "مدارک کسب‌وکار",
    DocumentType.SELFIE: "سلفی",
}
