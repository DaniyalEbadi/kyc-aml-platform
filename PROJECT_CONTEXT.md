# PROJECT_CONTEXT.md

## Project Purpose
Production-grade Persian/Farsi KYC (Know Your Customer), AML (Anti-Money Laundering), Identity Verification, Risk Analysis, and Compliance Intelligence platform for financial institutions.

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115.6
- **Language**: Python 3.12+
- **Database**: PostgreSQL 16 (SQLAlchemy 2.0, Alembic)
- **Cache/Queue**: Redis 7 + Celery 5.4
- **Auth**: JWT (HS256) with Access/Refresh tokens, bcrypt
- **Validation**: Pydantic v2
- **Logging**: structlog (JSON)
- **Observability**: Prometheus client
- **Testing**: pytest + pytest-asyncio

### Frontend
- **Framework**: Next.js 14.2 (App Router)
- **Language**: TypeScript 5.7 (strict mode)
- **Styling**: Tailwind CSS 3.4 + CSS Variables
- **UI Components**: shadcn/ui inspired (custom)
- **Charts**: Recharts 2.15
- **Forms**: React Hook Form 7.54 + Zod 3.24
- **State**: TanStack Query 5.62
- **Animation**: Framer Motion 11.15
- **Icons**: Lucide React 0.468
- **Date**: date-fns 4.1 (Jalali via custom utils)

### Infrastructure
- **Container**: Docker + Docker Compose
- **Storage**: Local filesystem (S3-compatible abstraction ready)
- **Reverse Proxy**: Nginx (production)

## Architecture

### Backend Layer Structure
```
backend/app/
├── api/routes/          # FastAPI route handlers (13 modules)
├── ai/                  # AI Provider Abstractions
│   ├── llm.py           # LLMProvider + MockLLMProvider
│   ├── ocr.py           # OCRProvider + MockOCRProvider + DocumentProcessor
│   └── vision.py        # VisionProvider + MockVisionProvider
├── aml/                 # AML Screening
│   └── screening.py     # ScreeningProvider + MockScreeningProvider
├── audit/               # Audit Logging
│   └── service.py       # write_audit()
├── core/                # Core Infrastructure
│   ├── config.py        # Pydantic Settings
│   ├── security.py      # JWT, bcrypt, passwords
│   ├── errors.py        # APIError, handlers
│   ├── logging.py       # structlog + RequestIdMiddleware
│   └── ratelimit.py     # In-memory sliding window
├── db/                  # Database Layer
│   ├── base.py          # DeclarativeBase
│   └── session.py       # Engine, SessionLocal, get_db
├── documents/           # Document Quality
│   └── quality.py       # QualityReport + analyze_image_bytes
├── domain/              # Business Logic (Pure Python)
│   ├── decisions.py     # decide() - deterministic boundary
│   ├── enums.py         # StrEnums + Persian translations
│   ├── risk.py          # compute_risk() - explainable scoring
│   └── rules.py         # Validation rules (Iranian NID, etc.)
├── integrations/        # External Integrations
│   └── storage.py       # LocalStorage + virus_scan_hook
├── models/              # SQLAlchemy ORM Models (22 entities)
│   └── entities.py      # All table definitions
├── rag/                 # Policy RAG
│   └── retriever.py     # PolicyRetriever (token overlap)
├── schemas/             # Pydantic Request/Response Models
├── services/            # Business Services
│   └── kyc.py           # Core KYC workflows
└── workers/             # Background Jobs
    ├── celery_app.py    # Celery configuration
    ├── jobs.py          # Job CRUD + dispatch
    └── pipeline.py      # Document processing pipeline
```

### Frontend Structure
```
frontend/
├── app/
│   ├── (auth)/login/    # Login page
│   ├── (dashboard)/     # Protected dashboard routes
│   │   ├── dashboard/   # Main dashboard with KPIs/charts
│   │   ├── customers/   # Customer list + detail
│   │   ├── applications/# Application list + detail (7 tabs)
│   │   ├── cases/       # Case queue + review workflow
│   │   ├── documents/   # Document list
│   │   ├── verification/# Face + document verification
│   │   ├── risk/        # Risk distribution + table
│   │   ├── aml/         # Screening matches
│   │   ├── analytics/   # BI dashboard
│   │   ├── policies/    # Policy management + search
│   │   ├── audit/       # Audit log viewer
│   │   ├── settings/    # Profile + password + logout
│   │   └── notifications/# Notification center
│   └── onboarding/      # 10-step onboarding wizard
├── components/
│   ├── ui/              # Base components (Button, Card, etc.)
│   ├── charts/          # Chart wrappers
│   ├── dashboard/       # KPICard, StatCard, ChartCard
│   ├── forms/           # Form components
│   ├── navigation/      # Sidebar, Header
│   └── tables/          # DataTable components
├── lib/
│   ├── api.ts           # ApiClient class
│   ├── utils.ts         # cn(), Persian digits, status maps
│   └── hooks.ts         # useAuth, useNotifications
├── hooks/               # Additional custom hooks
└── types/               # TypeScript interfaces
```

## Database Schema (22 Tables)

### Core Entities
- **users** - System users (5 roles: applicant, analyst, reviewer, admin, auditor)
- **customers** - KYC applicants (linked to users)
- **applications** - Onboarding applications (10 statuses)
- **documents** - Uploaded files (7 types, 5 statuses)
- **document_versions** - Version control
- **extracted_fields** - OCR extracted data with confidence

### Verification & Risk
- **verifications** - OCR, face verification records
- **face_verifications** - Similarity, quality, decision
- **risk_assessments** - Score (0-100), level, recommended decision
- **risk_factors** - Individual risk factors with weights
- **screening_results** - AML/PEP/Sanctions/Adverse Media

### Policy & Compliance
- **policies** - Policy documents
- **policy_versions** - Versioned policy bodies
- **policy_chunks** - RAG chunks with embeddings

### Case Management
- **cases** - Review cases (6 statuses, 4 priorities, SLA)
- **case_assignments** - Reviewer assignments
- **reviews** - Review actions with reasons

### Audit & Operations
- **decisions** - Final decisions with policy clauses
- **audit_events** - Immutable audit trail (actor, action, entity, state diff)
- **notifications** - User notifications
- **jobs** - Background job tracking
- **ai_evaluations** - AI output logging for governance
- **refresh_tokens** - JWT refresh token store

## Key Business Logic

### Deterministic Validation (domain/rules.py)
1. **Iranian National ID** - Checksum algorithm (10-digit)
2. **Identity Expiry** - Document must not be expired
3. **Name Consistency** - Fuzzy match (rapidfuzz token_set_ratio ≥ 82)
4. **Proof of Address Age** - ≤ 90 days
5. **Document Quality** - Threshold ≥ 45
6. **Face Similarity** - Threshold ≥ 0.62

### Risk Scoring (domain/risk.py)
Base: 8 + jurisdiction_risk (8-12)
Factors:
- Validation failures: per-check impact
- Quality < 55: +14
- Face < 0.62: +22
- PEP match: +35
- Sanctions match: +50
- High volume: +8
- Anomalies: +6 each

Levels: LOW (<35), MEDIUM (35-59), HIGH (60-79), CRITICAL (≥80)

### Decision Boundary (domain/decisions.py)
- Sanctions/PEP/CRITICAL → UNDER_REVIEW (auto)
- HIGH/escalation → UNDER_REVIEW (auto)
- Resubmission needed → RESUBMISSION_REQUESTED (auto)
- Else → APPROVED (auto)
- REJECTED only by human reviewer

### Document Pipeline (workers/pipeline.py)
1. Quality Analysis (Pillow-based)
2. OCR Extraction (Mock/Real provider)
3. Field Persistence (ExtractedField)
4. Screening (Sanctions/PEP/Adverse/Watchlist)
5. Risk Assessment
6. Decision Engine
7. Case Creation (if needed)
8. Notifications
9. Audit Logging

## API Endpoints (13 Route Modules)

| Module | Prefix | Key Endpoints |
|--------|--------|---------------|
| auth | /api/v1/auth | POST /login, POST /refresh, GET /me, POST /change-password |
| health | /api/v1/health | GET / |
| customers | /api/v1/customers | GET /, POST /, GET /{id}, PUT /{id}, POST /{id}/notes |
| applications | /api/v1/applications | GET /, POST /, GET /{id}, PUT /{id}, POST /{id}/submit |
| documents | /api/v1/documents | GET /, POST /upload, GET /{id}, GET /{id}/fields |
| verification | /api/v1/verification | POST /face, GET /face/{app_id}, GET /{app_id} |
| risk | /api/v1/risk | GET /{app_id} |
| screening | /api/v1/screening | GET /{app_id} |
| cases | /api/v1/cases | GET /, GET /{id}, POST /{id}/assign, POST /{id}/review, PUT /{id} |
| policies | /api/v1/policies | GET /, GET /{id}, POST /, POST /search |
| audit | /api/v1/audit | GET /, GET /{entity}/{entity_id} |
| analytics | /api/v1/analytics | GET /, GET /reviewer-workload |
| notifications | /api/v1/notifications | GET /, POST /read |
| search | /api/v1/search | GET /?q= |
| jobs | /api/v1/jobs | GET /{job_id} |

## Frontend Pages

| Route | Description |
|-------|-------------|
| /login | Persian RTL login with demo credentials |
| /dashboard | KPIs, charts (area, pie, bar), funnel |
| /customers | Paginated table, search, detail modal |
| /customers/[id] | Profile, risk gauge, applications, notes |
| /applications | Filterable table, status badges |
| /applications/[id] | 7 tabs: overview, documents, verification, risk, screening, decisions, timeline |
| /cases | Card grid, filters, priority badges |
| /cases/[id] | Detail, reviews, assignments, review modal |
| /documents | Table with type/status badges |
| /verification/[id] | Face metrics, document verifications, quality |
| /risk | Pie chart, bar chart, risk table |
| /aml | Screening stats, matched results table |
| /analytics | Executive KPIs + 6 charts |
| /policies | Version tree, full-text search |
| /audit | Paginated event log, entity filter |
| /settings | Profile, password, logout |
| /notifications | List with read/unread, mark all read |
| /onboarding | 10-step wizard with progress bar |

## Development Commands

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000
npm run build        # Production build
npm run start        # Production server
npm run lint         # ESLint

# Docker
docker-compose up -d --build
docker-compose logs -f backend
docker-compose logs -f frontend

# Database
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| APP_NAME | Application name | پارس‌هویت |
| DEMO_MODE | Use mock providers | true |
| SECRET_KEY | JWT signing key | (required) |
| DATABASE_URL | PostgreSQL DSN | sqlite:///./storage/kyc.db |
| REDIS_URL | Redis DSN | redis://localhost:6379/0 |
| CELERY_BROKER_URL | Celery broker | redis://localhost:6379/1 |
| LLM_PROVIDER | llm provider | mock |
| OCR_PROVIDER | ocr provider | mock |
| VISION_PROVIDER | vision provider | mock |
| SCREENING_PROVIDER | screening provider | mock |
| STORAGE_BACKEND | local/s3 | local |
| MAX_UPLOAD_MB | File size limit | 12 |

## Security Principles

1. **No LLM Authority** - LLM never makes approve/reject decisions
2. **Deterministic Core** - Validation, risk, decisions are pure Python
3. **Immutable Audit** - All decisions logged with policy clauses
4. **RBAC Enforced** - Backend checks, not just frontend hiding
5. **File Security** - Type/size validation, virus scan hook, private storage
6. **Prompt Injection Defense** - Document content never controls system prompts
7. **Token Rotation** - Short-lived access (30m), refresh (7d), revocation

## AI Governance

Every AI evaluation stores:
- model_name, model_version, prompt_version
- policy_version, retrieved_evidence
- output, confidence
- reviewer_outcome, overridden flag

Enables regression testing and override analytics.

## Mock/Development Mode

All AI providers default to mock:
- **MockLLMProvider** - Returns policy-grounded explanations
- **MockOCRProvider** - Returns 10 Persian fields with simulated confidence
- **MockVisionProvider** - Deterministic similarity from hash comparison
- **MockScreeningProvider** - Fuzzy match against 2 sanctions + 2 PEP names

Seed data includes:
- 4 staff users (admin, analyst, reviewer, auditor)
- 60 customers with Persian names
- 120 applications across all statuses
- 57 cases with reviews/assignments
- 62 documents
- 1 policy with 6 chunks
- 50 audit events
- Notifications for staff

## Known Limitations

1. **No Real AI Providers** - Mock implementations only; production needs real API keys
2. **In-Memory Rate Limit** - Not distributed; use Redis-based for multi-instance
3. **SQLite Default** - Demo uses SQLite; PostgreSQL required for production
4. **No Email/Notification Delivery** - In-app only; integrate SendGrid/Twilio for production
5. **No WebSocket** - Polling for job status; add SSE for real-time
6. **Single-Language** - Persian only; i18n structure not implemented
7. **No File Preview** - Document viewer not implemented
8. **Limited Test Coverage** - Backend tests exist but need expansion

## Future Enhancements

- [ ] Real OCR integration (Tesseract, Azure Form Recognizer, Google Document AI)
- [ ] Real Face Recognition (ArcFace, FaceNet, AWS Rekognition)
- [ ] Real AML Screening (World-Check, Dow Jones, Refinitiv)
- [ ] Liveness Detection (passive/active)
- [ ] pgvector for semantic policy search
- [ ] WebSocket for real-time job updates
- [ ] Email/SMS notification delivery
- [ ] Advanced RBAC with permissions matrix
- [ ] Multi-tenant architecture
- [ ] Comprehensive test suite (unit, integration, e2e)
- [ ] OpenTelemetry distributed tracing
- [ ] Kubernetes deployment manifests

## File Ownership

- **Backend**: `backend/` - FastAPI application
- **Frontend**: `frontend/` - Next.js application
- **Reference**: `_upstream/` - Original kyc-onboarding-agent (MIT licensed)
- **Config**: Root `.env.example`, `docker-compose.yml`, `README.md`