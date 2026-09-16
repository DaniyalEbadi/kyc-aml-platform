# ARCHITECTURE.md

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PARSHEID KYC/AML PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    HTTPS/REST    ┌──────────────┐    SQL/Redis    ┌──────┐ │
│  │   Next.js    │ ◀──────────────▶ │   FastAPI    │ ◀─────────────▶ │Postgre│ │
│  │  (Frontend)  │   API v1         │  (Backend)   │   Alembic       │ SQL  │ │
│  │  Port: 3000  │                  │  Port: 8000  │                 │      │ │
│  └──────────────┘                  └──────┬───────┘                 └──────┘ │
│                                            │                                     │
│                    ┌───────────────────────┼───────────────────────┐            │
│                    ▼                       ▼                       ▼            │
│             ┌─────────────┐         ┌─────────────┐         ┌─────────────┐    │
│             │    Redis    │         │   Celery    │         │   Storage   │    │
│             │  (Cache/    │         │  (Workers)  │         │  (Local/    │    │
│             │   Broker)   │         │             │         │   S3)       │    │
│             └─────────────┘         └─────────────┘         └─────────────┘    │
│                    │                       │                       │            │
│                    └───────────────────────┼───────────────────────┘            │
│                                            ▼                                     │
│                              ┌─────────────────────────────┐                     │
│                              │     AI Providers            │                     │
│                              │  LLM • OCR • Vision • Embed │                     │
│                              │  (Mock / Real Adapters)     │                     │
│                              └─────────────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Backend Architecture (Clean Architecture)

### Layer Separation

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER (FastAPI Routes)               │
│  auth, customers, applications, documents, verification,        │
│  risk, screening, cases, policies, audit, analytics,            │
│  notifications, search, jobs, health                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER (Business Logic)             │
│  services/kyc.py - Core workflows                               │
│  workers/pipeline.py - Document processing pipeline             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER (Pure Python)                 │
│  domain/                                                        │
│  ├── decisions.py  - decide()          # Deterministic boundary │
│  ├── risk.py       - compute_risk()    # Explainable scoring    │
│  ├── rules.py      - validate_*()      # Validation rules       │
│  └── enums.py      - StrEnums + Persian translations            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   DATA LAYER    │ │  AI LAYER       │ │  INTEGRATIONS   │
│  (Repositories) │ │  (Providers)    │ │  (External)     │
│                 │ │                 │ │                 │
│ models/         │ │ ai/             │ │ integrations/   │
│ db/session.py   │ │ ├── llm.py      │ │ ├── storage.py  │
│                 │ │ ├── ocr.py      │ │                 │
│                 │ │ ├── vision.py   │ │                 │
│                 │ │ aml/            │ │                 │
│                 │ │ └── screening.py│ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Key Design Principles

1. **Business Logic Separation** - Domain logic in `domain/` has zero FastAPI/SQLAlchemy dependencies
2. **Provider Abstraction** - All AI/External services behind interfaces (`LLMProvider`, `OCRProvider`, etc.)
3. **Single Source of Truth** - Validation, risk, decisions in domain layer only
4. **Deterministic Decisions** - LLM never makes approve/reject; only explains
5. **Immutable Audit** - All state changes logged before communication

## Frontend Architecture

### Route Structure (Next.js App Router)

```
app/
├── layout.tsx                 # Root: RTL, Vazirmatn, metadata
├── page.tsx                   # Redirect to /login
├── globals.css                # Tailwind + CSS Variables + Dark mode
├── (auth)/
│   ├── layout.tsx             # Public layout
│   └── login/page.tsx         # Login form
├── (dashboard)/
│   ├── layout.tsx             # Auth check + Sidebar + Header
│   ├── dashboard/page.tsx     # KPIs + Charts
│   ├── customers/page.tsx     # List with search/pagination
│   ├── customers/[id]/page.tsx# Detail: info, risk, apps, notes
│   ├── applications/page.tsx  # Filterable table
│   ├── applications/[id]/page.tsx # 7 tabs
│   ├── cases/page.tsx         # Card grid
│   ├── cases/[id]/page.tsx    # Review workflow
│   ├── documents/page.tsx     # Table
│   ├── verification/[id]/page.tsx # Face + doc quality
│   ├── risk/page.tsx          # Distribution + table
│   ├── aml/page.tsx           # Screening matches
│   ├── analytics/page.tsx     # Executive BI
│   ├── policies/page.tsx      # Version tree + search
│   ├── audit/page.tsx         # Event log
│   ├── settings/page.tsx      # Profile + password
│   └── notifications/page.tsx # Notification center
└── onboarding/page.tsx        # 10-step wizard
```

### Component Architecture

```
components/
├── navigation/
│   ├── sidebar.tsx      # Fixed RTL sidebar with sections
│   └── header.tsx       # Global search + notifications + logout
├── dashboard/
│   ├── KPICard.tsx      # Icon + value + label
│   ├── StatCard.tsx     # Label + value
│   └── ChartCard.tsx    # Title + chart wrapper
├── ui/                  # Base primitives (Button, Input, Card, etc.)
├── charts/              # Recharts wrappers
├── forms/               # FormField, Select, Upload, etc.
└── tables/              # DataTable with sorting/pagination
```

### State Management

- **Server State**: TanStack Query (React Query) - caching, invalidation, background refetch
- **Client State**: React useState/useReducer
- **Auth**: Custom `useAuth` hook with localStorage token persistence
- **Notifications**: Custom `useNotifications` hook with polling

### Theming System

```css
/* CSS Variables (globals.css) */
:root { /* Light mode */ }
.dark { /* Dark mode - default */ }

/* Tailwind Config */
darkMode: "class"
fontFamily: { vazir: ["Vazirmatn", "system-ui"] }
colors: { brand: {...} }  /* Primary color scale */
```

### RTL Implementation

1. `<html dir="rtl" lang="fa">` in root layout
2. Flexbox/Grid with logical properties (`ms-`, `me-` instead of `ml-`, `mr-`)
3. Text alignment: `text-right` default
4. Icons: Chevron directions reversed
5. Charts: Recharts supports RTL via `direction="rtl"` in tooltips

## Data Flow

### Onboarding Flow
```
User fills form (10 steps)
    │
    ▼
POST /api/v1/applications (create draft)
    │
    ▼
Upload documents → POST /api/v1/documents/upload
    │
    ▼
Celery Job: process_document_job
    │
    ├─▶ Quality Analysis
    ├─▶ OCR Extraction
    ├─▶ Screening (Sanctions/PEP/Adverse/Watchlist)
    ├─▶ Risk Assessment
    ├─▶ Decision Engine
    ├─▶ Case Creation (if UNDER_REVIEW)
    ├─▶ Notifications
    └─▶ Audit Logging
    │
    ▼
GET /api/v1/jobs/{id} (poll for status)
    │
    ▼
User submits → POST /api/v1/applications/{id}/submit
    │
    ▼
Review workflow (if needed) → /cases/{id}/review
```

### Verification Flow
```
Face Verification:
1. User uploads selfie
2. POST /api/v1/verification/face {app_id, selfie}
3. VisionProvider.compare(id_bytes, selfie_bytes)
4. Store FaceVerification record
5. Return similarity, quality, decision

Document Verification:
1. Document uploaded → processing job
2. OCR extracts fields with confidence
3. QualityReport generated
4. Risk engine uses extracted data
```

### Risk Assessment Flow
```
Input: ValidationBundle, quality_score, face_similarity, pep, sanctions, jurisdiction_risk, volume, anomalies
    │
    ▼
compute_risk() in domain/risk.py
    │
    ├─ Base: 8 + jurisdiction_risk
    ├─ Add validation failure impacts
    ├─ Quality < 55: +14
    ├─ Face < 0.62: +22
    ├─ PEP: +35
    ├─ Sanctions: +50
    ├─ Volume: +8
    └─ Anomalies: +6 each
    │
    ▼
Clamp 0-100 → RiskLevel (LOW/MEDIUM/HIGH/CRITICAL)
    │
    ▼
decide() in domain/decisions.py
    │
    ├─ Sanctions/PEP/CRITICAL → UNDER_REVIEW
    ├─ HIGH/escalation → UNDER_REVIEW
    ├─ Resubmission → RESUBMISSION_REQUESTED
    └─ Else → APPROVED
    │
    ▼
Persist RiskAssessment + RiskFactors + Decision
    │
    ▼
LLM Explanation (RAG-grounded)
    │
    ▼
Audit Event + AI Evaluation Log
```

## Database Design

### Key Relationships
```
User (1) ─────▶ (1) Customer (1) ─────▶ (N) Application
                                        │
                                        ├─▶ (N) Document
                                        ├─▶ (N) ApplicationEvent
                                        ├─▶ (N) RiskAssessment
                                        ├─▶ (N) ScreeningResult
                                        ├─▶ (N) Verification
                                        ├─▶ (N) FaceVerification
                                        ├─▶ (N) Decision
                                        └─▶ (N) Case
                                              │
                                              ├─▶ (N) CaseAssignment
                                              └─▶ (N) Review
```

### Indexing Strategy
- Primary keys: UUID (String 36)
- Foreign keys: Indexed
- Composite indexes: `ix_app_status_created`, `ix_case_status_priority`, `ix_audit_entity`
- Search columns: `national_id`, `passport_number`, `email`, `application_number`, `case_number`

## Security Architecture

### Authentication
```
┌─────────────┐     1. POST /login      ┌─────────────┐
│   Client    │ ──────────────────────▶ │   Server    │
└─────────────┘ ◀────────────────────── │             │
       │                                 │  Verify     │
       │ 2. Access Token (30m)           │  Password   │
       │ 3. Refresh Token (7d)           │  Create JWT │
       ▼                                 └─────────────┘
┌─────────────┐
│  Requests   │ ──▶ Authorization: Bearer <access>
│  with JWT   │
└─────────────┘
       │
       │ 4. 401 → POST /refresh with refresh token
       ▼
┌─────────────┐
│  New Token  │
└─────────────┘
```

### Authorization (RBAC)
```python
# Roles
RoleName.APPLICANT     # Customer self-service
RoleName.ANALYST       # Read + analytics
RoleName.REVIEWER      # Case review actions
RoleName.ADMIN         # Full access + user management
RoleName.AUDITOR       # Read-only audit access

# Dependency Injection
require_roles(RoleName.REVIEWER, RoleName.ADMIN)
```

### File Security
```python
# storage.py
1. Content-Type validation (image/jpeg, image/png, application/pdf)
2. Size limit (12MB default)
3. Extension allowlist (.jpg, .jpeg, .png, .pdf)
4. UUID filename generation
5. Path traversal prevention
6. Virus scan hook (EICAR test)
7. Private storage - no public URLs
```

## AI Provider Architecture

### Interface Pattern
```python
# Abstract base
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str: ...

# Mock implementation (default)
class MockLLMProvider(LLMProvider):
    def generate(self, system_prompt: str, user_message: str) -> str:
        # Parses decision from prompt, returns policy-grounded explanation

# Factory
def get_llm_provider(name: str) -> LLMProvider:
    return MockLLMProvider()  # Or real provider based on config
```

### Providers
| Type | Interface | Mock | Production Candidates |
|------|-----------|------|----------------------|
| LLM | `LLMProvider` | MockLLMProvider | Anthropic Claude, OpenAI GPT |
| OCR | `OCRProvider` | MockOCRProvider | Tesseract, Azure Form Recognizer, Google Document AI |
| Vision | `VisionProvider` | MockVisionProvider | ArcFace, FaceNet, AWS Rekognition |
| Embedding | `EmbeddingProvider` | MockEmbeddingProvider | sentence-transformers, OpenAI, Cohere |
| Screening | `ScreeningProvider` | MockScreeningProvider | World-Check, Dow Jones, Refinitiv |

## Background Job Processing

### Celery Configuration
```python
# workers/celery_app.py
celery_app = Celery("kyc", broker=..., backend=...)
celery_app.conf.task_serializer = "json"

@celery_app.task(name="process_document_task")
def process_document_task(job_id: str):
    process_document_job(job_id)
```

### Job Pipeline
```python
# workers/pipeline.py
def process_document_job(job_id: str):
    1. Update job: RUNNING, 10%, "در حال پردازش..."
    2. Read file from storage
    3. Update: 25%, "بررسی کیفیت..."
    4. quality = analyze_image_bytes()
    5. Update: 50%, "استخراج اطلاعات..."
    6. ocr = DocumentProcessor.extract()
    7. Save ExtractedFields
    8. Save Verification (OCR)
    9. Update: 70%, "غربالگری و ریسک..."
    10. run_verification_suite()
    11. Update: SUCCEEDED, 100%, "تکمیل شد"
```

### Inline Mode (Development)
```python
# workers/jobs.py
def dispatch_document_job(job_id: str):
    if settings.inline_jobs:  # True in dev
        process_document_job(job_id)  # Synchronous
    else:
        process_document_task.delay(job_id)  # Celery
```

## Observability

### Structured Logging
```python
# core/logging.py
structlog.configure(
    processors=[
        merge_contextvars,
        add_log_level,
        TimeStamper(fmt="iso"),
        JSONRenderer(),
    ]
)

# RequestIdMiddleware adds request_id to all logs
```

### Health Checks
```python
# api/routes/health.py
GET /api/v1/health → {"status": "healthy", "app": "پارس‌هویت", "demo_mode": true}
```

### Metrics (Prometheus)
```python
# Add prometheus_client metrics
# /metrics endpoint for scraping
```

## Deployment Architecture

### Docker Compose Services
```yaml
services:
  postgres:    # postgres:16-alpine, healthcheck
  redis:       # redis:7-alpine, healthcheck
  backend:     # FastAPI + Uvicorn + alembic + seed
  worker:      # Celery worker
  frontend:    # Next.js standalone
```

### Production Considerations
1. **SSL/TLS** - Nginx reverse proxy with certs
2. **Secrets** - Docker secrets or Vault, not .env
3. **Database** - Managed PostgreSQL (RDS, Cloud SQL)
4. **Redis** - Cluster mode for HA
5. **Storage** - S3/MinIO for documents
4. **Monitoring** - Prometheus + Grafana + Alertmanager
5. **Logging** - ELK/Loki for centralized logs
6. **CI/CD** - GitHub Actions / GitLab CI
7. **Backup** - Automated PG backups + point-in-time recovery

## API Design Standards

### Response Format
```json
// Success
{ "items": [...], "total": 100, "page": 1, "page_size": 20 }

// Error
{ "code": "not_found", "message": "مشتری یافت نشد.", "details": {} }
```

### Pagination
- Query params: `page`, `page_size` (max 100)
- Response: `items`, `total`, `page`, `page_size`

### Filtering/Sorting
- `?status=approved&risk_level=high&search=ali`
- `?sort_by=created_at&sort_order=desc`

### Versioning
- URL prefix: `/api/v1/`
- Backward compatible additions only

## Testing Strategy

### Backend
```bash
# Unit tests
pytest tests/ -v

# Key test areas:
# - domain/rules.py (validation logic)
# - domain/risk.py (scoring)
# - domain/decisions.py (boundary)
# - services/kyc.py (workflows)
# - api/routes/*.py (endpoints)
```

### Frontend
```bash
# Linting
npm run lint

# Type checking
npx tsc --noEmit

# Build verification
npm run build
```

## Performance Considerations

1. **Database**
   - Connection pooling (SQLAlchemy default)
   - Selective loading (joinedload for relationships)
   - Composite indexes on query patterns

2. **Frontend**
   - Next.js static generation where possible
   - TanStack Query caching (5min staleTime)
   - Code splitting by route
   - Image optimization (next/image)

3. **Background Jobs**
   - Celery concurrency tuning
   - Job result TTL
   - Priority queues for high-risk cases

## Extensibility Points

1. **New Document Types** - Add to `DocumentType` enum + OCR mapping
2. **New Screening Lists** - Add to `ScreeningKind` + provider implementation
3. **New Risk Factors** - Add to `compute_risk()` + `RiskFactor` model
4. **New Decision Codes** - Add to `DecisionCode` + `decide()` logic
5. **New AI Providers** - Implement interface + register in factory
6. **New Policy Sources** - Extend `PolicyRetriever` for new formats
7. **New Notification Channels** - Extend `Notification` model + delivery service