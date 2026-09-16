from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.domain.enums import (
    ApplicationStatus, CasePriority, CaseStatus, DecisionCode,
    DocumentType, RiskLevel, RoleName
)
from app.models.entities import (
    Application, ApplicationEvent, Case, CaseAssignment,
    Customer, CustomerNote, Decision, Document, DocumentVersion,
    ExtractedField, Job, Notification, Policy,
    PolicyChunk, PolicyVersion, Review, RiskAssessment, RiskFactor,
    ScreeningResult, User, Verification, AuditEvent
)

PERSIAN_FIRST_NAMES_M = [
    "امیر", "محمد", "علی", "رضا", "حسین", "حسن", "مهدی", "احمد", "سعید", "امیرحسین",
    "محمدامین", "یوسف", "کامران", "میلاد", "بهزاد", "فرهاد", "پوریا", "آریان", "نیما", "بهرام",
]
PERSIAN_FIRST_NAMES_F = [
    "زهرا", "فاطمه", "سارا", "مریم", "نرگس", "النا", "یسنا", "مهسا", "سمیرا", "نیلوفر",
    "ریحانه", "ترانه", "پریسا", "الهه", "بهار", "ندا", "مینا", "دنا", "آوا", "کیمیا",
]
PERSIAN_LAST_NAMES = [
    "احمدی", "محمدی", "رضایی", "حسینی", "کریمی", "فیروزی", "moradi",
    "نجفی", "jafari", "ulkordestani", "parsa", "rahimi", "hosseini",
    "akbari", "mousavi", "hashemi", "fazel", "karimi", "nouri", "salehi",
]
PROVINCES = ["تهران", "اصفهان", "شیراز", "تبریز", "مشهد", "اهواز", "کرمان", "یزد", "اردبیل", "بروجرد"]
CITIES = ["تهران", "اصفهان", "شیراز", "تبریز", "مشهد", "اهواز", "کرمان", "یزد", "قزوین", "همدان"]
OCCUPATIONS = ["مهندس", "پزشک", "وکیل", "حسابدار", "معلم", "بازرگان", "کارمند", "دانشجو", "آزاد", "مشاور"]
INCOME_RANGES = ["زیر ۱۰ میلیون", "۱۰-۲۰ میلیون", "۲۰-۵۰ میلیون", "۵۰-۱۰۰ میلیون", "بالای ۱۰۰ میلیون"]
VOLUMES = ["پایین", "متوسط", "بالا"]
FUND_SOURCES = ["حقوق", "سود سرمایه", "بازرگانی", "اجاره", "ارث", "other"]


def random_national_id() -> str:
    base = "".join([str(random.randint(0, 9)) for _ in range(9)])
    total = sum(int(base[i]) * (10 - i) for i in range(9))
    rem = total % 11
    check = rem if rem < 2 else 11 - rem
    return base + str(check)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(User).count()
        if existing > 0:
            print(f"Seed skipped: {existing} users already exist.")
            return

        now = datetime.now(timezone.utc)

        admin = User(
            email="admin@parsheid.ir",
            full_name="مدیر سامانه",
            hashed_password=hash_password("admin123"),
            role=RoleName.ADMIN.value,
        )
        analyst = User(
            email="analyst@parsheid.ir",
            full_name="تحلیلگر انطباق",
            hashed_password=hash_password("analyst123"),
            role=RoleName.ANALYST.value,
        )
        reviewer = User(
            email="reviewer@parsheid.ir",
            full_name="بررسی‌کننده ارشد",
            hashed_password=hash_password("reviewer123"),
            role=RoleName.REVIEWER.value,
        )
        auditor = User(
            email="auditor@parsheid.ir",
            full_name="حسابرس ارشد",
            hashed_password=hash_password("auditor123"),
            role=RoleName.AUDITOR.value,
        )
        staff_users = [admin, analyst, reviewer, auditor]
        db.add_all(staff_users)
        db.flush()

        customers = []
        for i in range(60):
            gender = random.choice(["مرد", "زن"])
            first = random.choice(PERSIAN_FIRST_NAMES_M if gender == "مرد" else PERSIAN_FIRST_NAMES_F)
            last = random.choice(PERSIAN_LAST_NAMES)
            c = Customer(
                first_name=first,
                last_name=last,
                national_id=random_national_id(),
                passport_number=f"{'A' if random.random() > 0.5 else 'B'}{random.randint(10000000, 99999999)}",
                birth_date=f"{random.randint(1340, 1380)}/{random.randint(1, 12):02d}/{random.randint(1, 28):02d}",
                gender=gender,
                nationality="ایران" if random.random() > 0.1 else random.choice(["افغانستان", "عراق", "سوریه", "ترکیه"]),
                province=random.choice(PROVINCES),
                city=random.choice(CITIES),
                address=f"خیابان {random.choice(['ولیعصر', 'انقلاب', 'آزادی', 'olla', 'ValiAsr'])} پلاک {random.randint(1, 200)}",
                phone=f"09{random.randint(100000000, 999999999)}",
                email=f"user{i:03d}@example.com",
                overall_risk_score=random.randint(0, 100),
                overall_risk_level=random.choice(list(RiskLevel)),
                created_at=now - timedelta(days=random.randint(0, 90)),
            )
            customers.append(c)
        db.add_all(customers)
        db.flush()

        # Phase 1: Create applications (no FK refs to other new rows)
        applications = []
        app_data = []  # (app, customer, risk_level, created, status)
        for i in range(120):
            c = random.choice(customers)
            status = random.choice(list(ApplicationStatus))
            risk_level = random.choice(list(RiskLevel))
            created = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
            app = Application(
                application_number=f"APP-{1001 + i}",
                customer_id=c.id,
                status=status.value,
                source=random.choice(["web", "mobile", "branch"]),
                current_step=random.choice(["personal", "contact", "id_upload", "quality", "extraction", "review", "submit"]),
                declared_income=random.choice(INCOME_RANGES),
                source_of_funds=random.choice(FUND_SOURCES),
                occupation=random.choice(OCCUPATIONS),
                expected_volume=random.choice(VOLUMES),
                jurisdiction=random.choice(["ایران", "ترکیه", "امارات"]),
                submitted_at=created + timedelta(hours=1) if status != ApplicationStatus.DRAFT else None,
                decided_at=created + timedelta(days=2) if status in (ApplicationStatus.APPROVED, ApplicationStatus.REJECTED) else None,
                created_at=created,
                updated_at=created + timedelta(hours=random.randint(0, 48)),
            )
            applications.append(app)
            app_data.append((app, c, risk_level, created, status))
        db.add_all(applications)
        db.flush()  # Now all app.id values are populated

        # Phase 2: Create dependent records
        risk_assessments = []
        screening_results = []
        decisions = []
        case_list = []
        documents_list = []

        for app, c, risk_level, created, status in app_data:
            ra = RiskAssessment(
                application_id=app.id,
                score=random.randint(0, 100),
                level=risk_level.value,
                recommended_decision=random.choice(list(DecisionCode)).value,
                explanation="امتیاز ریسک توسط موتور قطعی محاسبه شد.",
                created_at=created,
            )
            risk_assessments.append(ra)

            for kind in ["sanctions", "pep", "adverse_media", "watchlist"]:
                sr = ScreeningResult(
                    application_id=app.id,
                    kind=kind,
                    matched=random.random() < 0.08,
                    score=random.uniform(0, 100),
                    list_name=f"f list {kind}",
                    is_simulated=True,
                    created_at=created,
                )
                screening_results.append(sr)

            dec = Decision(
                application_id=app.id,
                code=random.choice(list(DecisionCode)).value,
                source=random.choice(["policy_engine", "human_reviewer"]),
                reason="based on policy rules and risk assessment.",
                created_at=created,
            )
            decisions.append(dec)

            if status in (ApplicationStatus.IN_REVIEW, ApplicationStatus.ESCALATED, ApplicationStatus.APPROVED, ApplicationStatus.REJECTED):
                case = Case(
                    case_number=f"CASE-{len(case_list)+1:05d}",
                    application_id=app.id,
                    customer_id=c.id,
                    status=random.choice(list(CaseStatus)).value,
                    priority=random.choice(list(CasePriority)).value,
                    risk_level=risk_level.value,
                    assigned_to=random.choice([analyst.id, reviewer.id]),
                    sla_hours=random.choice([24, 48, 72]),
                    sla_due_at=created + timedelta(hours=random.choice([24, 48, 72])),
                    decision=random.choice(["approve", "reject", None]),
                    decision_reason="reviewed by compliance analyst." if random.random() > 0.5 else None,
                    created_at=created,
                )
                case_list.append(case)

            if random.random() < 0.6:
                doc_type = random.choice(list(DocumentType))
                doc = Document(
                    application_id=app.id,
                    customer_id=c.id,
                    doc_type=doc_type.value,
                    status=random.choice(["uploaded", "processing", "processed", "failed"]),
                    original_filename=f"{doc_type.value}_{app.application_number}.jpg",
                    content_type="image/jpeg",
                    size_bytes=random.randint(50000, 5000000),
                    storage_key=f"demo_{app.id}_{doc_type.value}.jpg",
                    is_simulated=True,
                    created_at=created,
                )
                documents_list.append(doc)

        db.add_all(risk_assessments)
        db.add_all(screening_results)
        db.add_all(decisions)
        db.add_all(case_list)
        db.add_all(documents_list)
        db.flush()

        # Notifications
        notifications = []
        for c in customers[:30]:
            for u in [admin, analyst, reviewer]:
                n = Notification(
                    user_id=u.id,
                    title=random.choice(["new case", "risk alert", "report ready", "review needed"]),
                    body=f"new operation for customer {c.first_name} {c.last_name}.",
                    kind=random.choice(["new_case", "high_risk", "report", "review_needed"]),
                    read=random.random() > 0.6,
                    created_at=now - timedelta(hours=random.randint(0, 72)),
                )
                notifications.append(n)
        db.add_all(notifications)

        # Audit events
        audit_events = []
        for i in range(50):
            ae = AuditEvent(
                actor_id=random.choice([u.id for u in staff_users]),
                actor_role=random.choice([u.role for u in staff_users]),
                action=random.choice(["application.create", "application.submit", "engine.decision", "case.assign", "review.action"]),
                entity=random.choice(["application", "case", "document"]),
                entity_id=str(random.randint(1, 100)),
                new_state={"status": random.choice(["submitted", "approved", "rejected", "in_review"])},
                reason="automated or manual operation.",
                created_at=now - timedelta(days=random.randint(0, 30)),
            )
            audit_events.append(ae)
        db.add_all(audit_events)

        # Policy
        policy = Policy(code="KYC-001", title="KYC Customer Onboarding Policy")
        db.add(policy)
        db.flush()
        pv = PolicyVersion(
            policy_id=policy.id, version="1.0", is_active=True,
            body="# KYC Policy\n\n## Section 1 - Identity Documents\n1.1 Acceptable documents: passport, national ID, driver license.\n1.2 Document must not be expired.\n\n## Section 2 - Proof of Address\n2.1 Utility bill or bank statement within 90 days.\n\n## Section 3 - Risk Tiering\n3.1 Customers risk-rated by country, income source, volume.\n3.2 Low/Medium: auto-approval allowed.\n3.3 High: mandatory human review."
        )
        db.add(pv)
        db.flush()
        for clause, section, text in [
            ("1.1", "Identity Documents", "Acceptable documents: passport, national ID, driver license."),
            ("1.2", "Identity Documents", "Document must not be expired."),
            ("2.1", "Proof of Address", "Utility bill or bank statement within 90 days."),
            ("3.1", "Risk Tiering", "Customers risk-rated by country, income source, volume."),
            ("3.2", "Risk Tiering", "Low/Medium: auto-approval allowed."),
            ("3.3", "Risk Tiering", "High: mandatory human review."),
        ]:
            db.add(PolicyChunk(version_id=pv.id, clause=clause, section=section, text=text))

        db.commit()
        print(f"Seed complete: {len(customers)} customers, {len(applications)} applications, {len(case_list)} cases, {len(documents_list)} documents.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
