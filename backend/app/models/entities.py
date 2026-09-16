from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uuid_str() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped["Customer | None"] = relationship(back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    national_id: Mapped[str | None] = mapped_column(String(20), index=True)
    passport_number: Mapped[str | None] = mapped_column(String(40), index=True)
    birth_date: Mapped[str | None] = mapped_column(String(16))
    gender: Mapped[str | None] = mapped_column(String(16))
    nationality: Mapped[str] = mapped_column(String(80), default="ایران")
    province: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    overall_risk_score: Mapped[int] = mapped_column(Integer, default=0)
    overall_risk_level: Mapped[str] = mapped_column(String(16), default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User | None] = relationship(back_populates="customer")
    applications: Mapped[list["Application"]] = relationship(back_populates="customer")
    notes: Mapped[list["CustomerNote"]] = relationship(back_populates="customer")


class CustomerNote(Base):
    __tablename__ = "customer_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    author_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped[Customer] = relationship(back_populates="notes")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_app_status_created", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="draft")
    source: Mapped[str] = mapped_column(String(32), default="web")
    current_step: Mapped[str] = mapped_column(String(32), default="personal")
    declared_income: Mapped[str | None] = mapped_column(String(80))
    source_of_funds: Mapped[str | None] = mapped_column(String(120))
    occupation: Mapped[str | None] = mapped_column(String(120))
    expected_volume: Mapped[str | None] = mapped_column(String(80))
    jurisdiction: Mapped[str] = mapped_column(String(80), default="ایران")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    customer: Mapped[Customer] = relationship(back_populates="applications")
    documents: Mapped[list["Document"]] = relationship(back_populates="application")
    events: Mapped[list["ApplicationEvent"]] = relationship(back_populates="application")
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="application")
    screenings: Mapped[list["ScreeningResult"]] = relationship(back_populates="application")
    cases: Mapped[list["Case"]] = relationship(back_populates="application")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="application")
    verifications: Mapped[list["Verification"]] = relationship(back_populates="application")


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="events")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(80))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(512))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document")
    fields: Mapped[list["ExtractedField"]] = relationship(back_populates="document")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    storage_key: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[Document] = relationship(back_populates="versions")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(64))
    field_label: Mapped[str] = mapped_column(String(80))
    value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    document: Mapped[Document] = relationship(back_populates="fields")


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    score: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="verifications")


class FaceVerification(Base):
    __tablename__ = "face_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    similarity: Mapped[float] = mapped_column(Float)
    quality_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(32))
    reasons: Mapped[list | None] = mapped_column(JSON)
    liveness_ready: Mapped[bool] = mapped_column(Boolean, default=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(16), index=True)
    recommended_decision: Mapped[str] = mapped_column(String(48))
    explanation: Mapped[str] = mapped_column(Text)
    policy_version_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="risk_assessments")
    factors: Mapped[list["RiskFactor"]] = relationship(back_populates="assessment")


class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(160))
    weight: Mapped[int] = mapped_column(Integer)
    triggered: Mapped[bool] = mapped_column(Boolean)
    detail: Mapped[str] = mapped_column(Text)

    assessment: Mapped[RiskAssessment] = relationship(back_populates="factors")


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    matched: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0)
    list_name: Mapped[str | None] = mapped_column(String(120))
    matched_name: Mapped[str | None] = mapped_column(String(255))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="screenings")


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    versions: Mapped[list["PolicyVersion"]] = relationship(back_populates="policy")


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id"), index=True)
    version: Mapped[str] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    policy: Mapped[Policy] = relationship(back_populates="versions")
    chunks: Mapped[list["PolicyChunk"]] = relationship(back_populates="version")


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    version_id: Mapped[str] = mapped_column(ForeignKey("policy_versions.id"), index=True)
    clause: Mapped[str] = mapped_column(String(32))
    section: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON)

    version: Mapped[PolicyVersion] = relationship(back_populates="chunks")


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_case_status_priority", "status", "priority"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="open")
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    risk_level: Mapped[str] = mapped_column(String(16), default="medium")
    assigned_to: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    sla_hours: Mapped[int] = mapped_column(Integer, default=48)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision: Mapped[str | None] = mapped_column(String(48))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    application: Mapped[Application] = relationship(back_populates="cases")
    assignments: Mapped[list["CaseAssignment"]] = relationship(back_populates="case")
    reviews: Mapped[list["Review"]] = relationship(back_populates="case")


class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    case: Mapped[Case] = relationship(back_populates="assignments")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    case: Mapped[Case] = relationship(back_populates="reviews")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    code: Mapped[str] = mapped_column(String(48))
    source: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    policy_clauses: Mapped[list | None] = mapped_column(JSON)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_entity", "entity", "entity_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    actor_id: Mapped[str | None] = mapped_column(String(36), index=True)
    actor_role: Mapped[str | None] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    previous_state: Mapped[dict | None] = mapped_column(JSON)
    new_state: Mapped[dict | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    policy_version: Mapped[str | None] = mapped_column(String(32))
    model_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(48))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String(80), default="queued")
    entity_id: Mapped[str | None] = mapped_column(String(36), index=True)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AIEvaluation(Base):
    __tablename__ = "ai_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    application_id: Mapped[str | None] = mapped_column(String(36), index=True)
    model_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(40))
    prompt_version: Mapped[str] = mapped_column(String(40))
    policy_version: Mapped[str | None] = mapped_column(String(40))
    retrieved_evidence: Mapped[list | None] = mapped_column(JSON)
    output: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    reviewer_outcome: Mapped[str | None] = mapped_column(String(48))
    overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
