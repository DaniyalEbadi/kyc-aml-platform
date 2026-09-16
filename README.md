# پارس‌هویت | ParsHeid KYC/AML Platform

سامانه جامع احراز هویت، مبارزه با پولشویی و مدیریت ریسک برای موسسات مالی

## ویژگی‌های اصلی

### 🔐 احراز هویت و KYC
- **جاده‌دهی اشتراک‌گذاری (Onboarding Wizard)** - ۱۰ مرحله کامل به زبان فارسی
- **بارگذاری و پردازش مدرک** - پشتیبانی از پاسپورت، کارت ملی، گواهینامه، مدرک نشانی
- **OCR و استخراج اطلاعات** - استخراج خودکار فیلدها با امتیاز اطمینان
- **بررسی کیفیت تصویر** - تحلیل تار، درخشش، روشنایی، کنتراست، برش، رزولوشن
- **تطبیق چهره (Face Verification)** - مقایسه سلفی با عکس مدرک با امتیاز شباهت
- **تشخیص زنده‌بودن (Liveness-Ready)** - معماری آماده برای اتصال لاینس

### ⚖️ مدیریت ریسک و انطباق
- **موتور ریسک قطعی** - محاسبه امتیاز ۰-۱۰۰ با عوامل قابل توضیح
- **مرزبندی تصمیم‌گیری** - قوانین قطعی برای تأیید/رد/ارجاع (LLM تصمیم نهایی نمی‌گیرد)
- **غربالگری AML/PEP/تحریم‌ها** - معماری متصل به ارائه‌دهندگان خارجی
- **سیاست‌محور (Policy-Driven)** - RAG برای بازیابی بندهای سیاست و استناد
- **نمودار تصمیم** - سیستم Case Management کامل

### 📊 هوش تجاری و آنالیتیکس
- **داشبورد مدیریتی** - ۱۲+ KPI اصلی
- **نمودارهای تعاملی** - Recharts با پشتیبانی RTL
- **قیف احراز هویت** - بصری‌سازی مراحل پردازش
- **توزیع ریسک** - نمودار دایره‌ای و میله‌ای
- **وظایف بررسی‌کننده** - بار کاری و SLA
- **تحلیل‌های پیشرفته** - توزیع زمان پردازش، توزیع اطمینان OCR، شباهت چهره

### 🔒 امنیت و ممیزی
- **اعتبارسنجی JWT** - Access/Refresh tokens با انقضا
- **RBAC** - ۵ نقش: متقاضی، تحلیلگر، بررسی‌کننده، مدیر، حسابرس
- **ممیزی تغییر‌نکردنی** - ثبت تمام رویدادها با نسخه سیاست و مدل
- **احراز هویت فایل** - اسکن ویروس، اعتبارسنجی نوع، نام‌گذاری امن
- **محدودیت نرخ** - Rate limiting در سطح میدل‌ور

### 🎨 تجربه کاربری
- **کاملاً RTL** - راست‌چین با فونت وزیرمتن
- **حالت تیره پیش‌فرض** - طراحی حرفه‌ای فین‌تک
- **واکنش‌گرا** - دسکتاپ، تبلت، موبایل
- **دسترسی‌پذیر** - HTML معنایی، ناوبری با کیبورد
- **انیمیشن‌های ظریف** - Framer Motion

## معماری سیستم

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js 14    │────▶│    FastAPI      │────▶│   PostgreSQL    │
│   (Frontend)    │     │    (Backend)    │     │   (Database)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │       │       │
                              ▼       ▼       ▼
                        ┌─────────────────────────────┐
                        │  Redis + Celery Workers     │
                        │  (Async Processing)         │
                        └─────────────────────────────┘
                              │       │       │
                              ▼       ▼       ▼
                        ┌─────────────────────────────┐
                        │  AI Providers (Mock/Real)   │
                        │  LLM • OCR • Vision • Embed │
                        └─────────────────────────────┘
```

## پشته تکنولوژی

### بک‌اند
- **FastAPI** - API nhanh و مدرن
- **SQLAlchemy 2.x** - ORM ناهمگام
- **Alembic** - مهاجرت‌های دیتابیس
- **Pydantic v2** - اعتبارسنجی داده‌ها
- **Celery + Redis** - صف کارها
- **Pytest** - تست واحد

### فرانت‌اند
- **Next.js 14 (App Router)** - فریم‌ورک React
- **TypeScript** - تایپ‌گذاری استاتیک
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - کامپوننت‌های قابل دسترس
- **Recharts** - نمودارهای تعاملی
- **React Hook Form + Zod** - فرم‌ها و اعتبارسنجی
- **TanStack Query** - مدیریت حالت سرور

### زیرساخت
- **Docker + Docker Compose** - کانتینری‌سازی
- **PostgreSQL 16** - دیتابیس اصلی
- **Redis 7** - کش و بروکر پیام

## شروع سریع

### پیش‌نیازها
- Docker و Docker Compose
- Git

### اجرا با Docker
```bash
# کلون مخزن
git clone <repository-url>
cd kyc-aml-platform

# کپی فایل محیط
cp .env.example .env

# اجرای سرویس‌ها
docker-compose up -d --build

# بررسی لاگ‌ها
docker-compose logs -f backend
```

### دسترسی به برنامه
- **فرانت‌اند**: http://localhost:3000
- **بک‌اند API**: http://localhost:8000
- **مستندات API**: http://localhost:8000/api/docs
- **دیتابیس**: localhost:5432 (kyc/kyc)

### حساب‌های پیش‌فرض (Demo Mode)
| نقش | ایمیل | گذرواژه |
|------|--------|----------|
| مدیر | admin@parsheid.ir | admin123 |
| تحلیلگر | analyst@parsheid.ir | analyst123 |
| بررسی‌کننده | reviewer@parsheid.ir | reviewer123 |
| حسابرس | auditor@parsheid.ir | auditor123 |

## توسعه محلی

### بک‌اند
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

### فرانت‌اند
```bash
cd frontend
npm install
npm run dev
```

## متغیرهای محیطی

فایل `.env.example` شامل تمام تنظیمات است:

```env
# برنامه
APP_NAME=پارس‌هویت
APP_ENV=development
DEMO_MODE=true
SECRET_KEY=change-me-in-production

# دیتابیس
DATABASE_URL=postgresql+psycopg://kyc:kyc@localhost:5432/kyc

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# AI Providers (mock برای توسعه)
LLM_PROVIDER=mock
OCR_PROVIDER=mock
VISION_PROVIDER=mock
SCREENING_PROVIDER=mock

# ذخیره‌سازی
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./storage/files
```

## ساختار پروژه

```
kyc-aml-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # API endpoints
│   │   ├── ai/                  # AI provider abstractions
│   │   ├── aml/                 # AML screening
│   │   ├── audit/               # Audit logging
│   │   ├── core/                # Config, security, errors
│   │   ├── db/                  # Database session
│   │   ├── documents/           # Document processing
│   │   ├── domain/              # Business logic (risk, rules, decisions)
│   │   ├── integrations/        # External integrations
│   │   ├── models/              # SQLAlchemy models
│   │   ├── rag/                 # Policy RAG
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business services
│   │   └── workers/             # Celery workers
│   ├── alembic/                 # Migrations
│   ├── tests/                   # Tests
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/              # React components
│   │   ├── ui/                  # Base UI components
│   │   ├── charts/              # Chart components
│   │   ├── dashboard/           # Dashboard components
│   │   ├── forms/               # Form components
│   │   ├── navigation/          # Sidebar, Header
│   │   └── tables/              # Table components
│   ├── lib/                     # Utilities, API client, hooks
│   ├── hooks/                   # Custom React hooks
│   └── types/                   # TypeScript types
├── _upstream/                   # Original reference project
├── docker-compose.yml
└── .env.example
```

## مفاهیم کلیدی

### موتور تصمیم‌گیری قطعی
سیستم **هرگز** از LLM برای تصمیم نهایی تأیید/رد استفاده نمی‌کند. تمام تصمیمات از طریق:
1. **قوانین اعتبارسنجی** (Iranian National ID، انقضا، تطابق نام، سن مدرک نشانی)
2. **محاسبه ریسک** (امتیاز ۰-۱۰۰ بر اساس عوامل صریح)
3. **مرزبندی تصمیم** (استراتژی эскаلیشن برای ریسک بالا/تحریم/PEP)

LLM تنها برای **توضیح** و **خلاصه‌سازی** بر اساس evidencia بازیابی شده استفاده می‌شود.

### RAG سیاست
- سیاست‌ها نسخه‌بندی می‌شوند
- متن به Chunkها تقسیم و در pgvector ذخیره می‌شود
- بازیابی با تداخل توکن (Token Overlap) + Embeddings
- هر توضیح AI به بند سیاست استناد می‌کند

### حالت توسعه (Demo Mode)
تمام ارائه‌دهندگان AI (LLM، OCR، Vision، Screening) به صورت Mock پیاده‌سازی شده‌اند. برای تولید:
1. کلیدهای API را در `.env` تنظیم کنید
2. `DEMO_MODE=false` قرار دهید
3. ارائه‌دهندگان واقعی را در `app/ai/` و `app/aml/` جایگزین کنید

## تست

```bash
# بک‌اند
cd backend
pytest -v

# فرانت‌اند
cd frontend
npm run lint
```

## مجوز

MIT License - 보며اساس پروژه اصلی [kyc-onboarding-agent](https://github.com/sachithpriyanga/kyc-onboarding-agent) ساخته شده است.

## تشکر
این پروژه بر پایه کار [sachithpriyanga](https://github.com/sachithpriyanga) در مخزن kyc-onboarding-agent توسعه یافته است.