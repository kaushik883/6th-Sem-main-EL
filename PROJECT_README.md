# LogiSight — Freight Audit & Invoice Management Platform

A comprehensive freight forwarding platform for managing quotes, invoices, charge masters, and anomaly detection with AI-powered copilot capabilities.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Working Features](#working-features)
4. [System Architecture](#system-architecture)
5. [Setup & Installation](#setup--installation)
6. [Running the Application](#running-the-application)
7. [User Roles & Permissions](#user-roles--permissions)
8. [API Endpoints](#api-endpoints)
9. [Database Schema](#database-schema)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

LogiSight is a multi-tenant SaaS platform designed for freight forwarding companies to:
- **Submit & Review Quotes** — Forwarders submit quotes, clients review and accept/reject
- **Manage Charge Masters** — Clients define standardized charges with auto-mapping
- **Upload & Extract Invoices** — Forwarders upload PDFs, system extracts charges via OCR
- **Detect Anomalies** — Automatic variance analysis between quotes and invoices
- **AI Copilot** — Natural language queries on freight data (Text-to-SQL)
- **Track Shipments** — Monitor shipment status and events

**Key Innovation**: Self-learning charge mapping system that improves with each manual correction.

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.13)
- **Database**: PostgreSQL (Neon serverless)
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT tokens (HS256)
- **PDF Extraction**: Veryfi API (OCR)
- **File Storage**: Cloudflare R2 (S3-compatible)
- **AI/LLM**: Google Gemini 2.5 Flash (via LangChain)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: TanStack Query (React Query)
- **UI Components**: Tailwind CSS + Lucide Icons
- **HTTP Client**: Axios with JWT interceptor

### Infrastructure
- **Database**: Neon PostgreSQL (serverless, free tier)
- **File Storage**: Cloudflare R2 (zero egress fees)
- **OCR Service**: Veryfi API (100 docs/month free)
- **LLM**: Google Gemini API (free tier available)

---

## ✅ Working Features

### 1. Authentication & Authorization
- ✅ JWT-based login/logout
- ✅ Role-based access control (RBAC)
- ✅ Multi-tenant data isolation
- ✅ 5 user roles: Super Admin, Client Admin, Client User, Forwarder Admin, Forwarder User

**Test Accounts** (all with password `password123`):
- Super Admin: `super@admin.com`
- Client Admin: `client@acme.com`
- Forwarder Admin: `forwarder@dhl.com`

### 2. Charge Master Management
- ✅ Create/edit/delete charges per company
- ✅ Add charge aliases (variations of charge names)
- ✅ Soft delete with `is_active` flag
- ✅ Company-scoped isolation
- ✅ Auto-suggest during quote/invoice entry

### 3. Quote Management
- ✅ Forwarder submits quotes with multiple charges
- ✅ Auto-generate unique quote reference numbers
- ✅ Automatic charge mapping (dictionary-based)
- ✅ Client reviews and accepts/rejects quotes
- ✅ Client can manually correct charge mappings
- ✅ Self-learning: corrected mappings auto-add as aliases

**Charge Mapping Tiers**:
- `DICTIONARY` — Exact match on charge name or aliases
- `UNMAPPED` — No match found in charge master
- `HUMAN` — Manually corrected by client

### 4. Invoice Management
- ✅ Forwarder uploads invoice PDFs for accepted quotes
- ✅ Veryfi API extracts invoice data (charge names, amounts, rates)
- ✅ Automatic charge mapping (same logic as quotes)
- ✅ PDF stored in Cloudflare R2 with public URL
- ✅ Client views extracted charges in table format
- ✅ Client can correct unmapped charges
- ✅ Per-charge variance display (invoice vs quote)

### 5. Anomaly Detection & Variance Analysis
- ✅ Client clicks "Analyse Invoice" to trigger analysis
- ✅ Detects 6 anomaly types:
  - `AMOUNT_MISMATCH` — Invoice amount ≠ quote amount
  - `RATE_MISMATCH` — Rate changed
  - `BASIS_MISMATCH` — Calculation basis changed (e.g., Per KG → Per Shipment)
  - `UNEXPECTED_CHARGE` — Charge in invoice but not in quote
  - `MISSING_CHARGE` — Charge in quote but not in invoice
  - `DUPLICATE_INVOICE` — Multiple invoices for same quote
- ✅ Per-charge variance calculation (red for overcharge, green for undercharge)
- ✅ Net variance summary (total invoice - total quote)
- ✅ Anomalies stored in database for audit trail
- ✅ Re-runnable analysis (clears old anomalies)

### 6. AI Copilot (Text-to-SQL)
- ✅ Natural language queries on freight data
- ✅ LangChain + Google Gemini for SQL generation
- ✅ Read-only query execution (safety guardrails)
- ✅ Multi-tenant isolation (users only see their company's data)
- ✅ Query timeout protection (8 seconds)
- ✅ Result row capping (max 200 rows)
- ✅ Natural language summarization of results

**Example Queries**:
- "Which forwarder had the most anomalies this month?"
- "What's the total value of accepted quotes?"
- "Show me invoices with amount mismatches"

### 7. Master Data Management
- ✅ Airports (IATA codes)
- ✅ Currencies (ISO codes)
- ✅ Countries
- ✅ Pre-seeded with 10 of each for testing

### 8. Dashboard & Analytics
- ✅ Key metrics display (pending quotes, invoices, anomalies)
- ✅ Role-specific views
- ✅ Company-scoped statistics

### 9. Tracking & Shipment Status
- ✅ List all shipments with current status
- ✅ View tracking events timeline
- ✅ Add tracking events (forwarder only)

---

## 🏗 System Architecture

### Folder Structure

```
LogiSight-main 2/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # API routes
│   │   │   ├── auth.py          # Login, logout, profile
│   │   │   ├── charges.py       # Charge master CRUD
│   │   │   ├── companies.py     # Company management
│   │   │   ├── quotes.py        # Quote submission & review
│   │   │   ├── invoices.py      # Invoice upload & analysis
│   │   │   ├── dashboard.py     # Dashboard stats
│   │   │   ├── copilot.py       # AI copilot endpoint
│   │   │   ├── tracking.py      # Shipment tracking
│   │   │   └── masters.py       # Master data (airports, currencies)
│   │   ├── core/
│   │   │   ├── config.py        # Settings & env vars
│   │   │   ├── database.py      # DB connection & session
│   │   │   ├── security.py      # JWT & password hashing
│   │   │   └── dependencies.py  # Auth middleware
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── services/            # Business logic
│   │   │   ├── veryfi_client.py # PDF extraction
│   │   │   ├── r2_storage.py    # Cloudflare R2 upload
│   │   │   ├── copilot.py       # LLM orchestration
│   │   │   └── copilot_*.py     # Copilot guardrails & executor
│   │   └── main.py              # FastAPI app setup
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment variables
│   └── .venv/                    # Virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts        # Axios API client
│   │   │   └── types.ts         # TypeScript interfaces
│   │   ├── pages/               # Page components
│   │   │   ├── Login.tsx
│   │   │   ├── Quotes.tsx
│   │   │   ├── QuoteForm.tsx
│   │   │   ├── QuoteDetail.tsx
│   │   │   ├── Invoices.tsx
│   │   │   ├── InvoiceAnalysis.tsx
│   │   │   ├── ChargeMaster.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Tracking.tsx
│   │   │   ├── Copilot.tsx
│   │   │   └── SuperAdmin/
│   │   ├── components/          # Reusable components
│   │   │   ├── ChargeLineTable.tsx
│   │   │   ├── AnomalyFlag.tsx
│   │   │   ├── ConfidenceBadge.tsx
│   │   │   └── Layout.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts       # Auth context
│   │   │   └── useQuery.ts      # TanStack Query setup
│   │   ├── providers/
│   │   │   └── AuthProvider.tsx # Auth state management
│   │   └── main.tsx
│   ├── package.json
│   ├── .env                      # Frontend env vars
│   └── vite.config.ts
│
├── database_schema.sql           # Complete PostgreSQL schema
├── PROJECT_README.md             # This file
└── .env                          # Root env (if needed)
```

### Data Flow

```
Forwarder submits Quote
    ↓
Backend auto-maps charges (dictionary lookup)
    ↓
Client reviews Quote
    ↓
Client accepts Quote
    ↓
Forwarder uploads Invoice PDF
    ↓
Veryfi extracts charges
    ↓
Backend auto-maps charges
    ↓
Client views Invoice with extracted charges
    ↓
Client clicks "Analyse Invoice"
    ↓
Backend compares invoice vs quote
    ↓
Anomalies detected & stored
    ↓
Client sees variance & anomalies
    ↓
Client can ask Copilot questions about the data
```

---

## 🚀 Setup & Installation

### Prerequisites

- **Python 3.13+** (with pip)
- **Node.js 18+** (with npm)
- **PostgreSQL** (or Neon account for serverless)
- **Git**

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd LogiSight-main\ 2
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

Create `backend/.env` with the following:

```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname

# Veryfi API (for PDF extraction)
VERYFI_CLIENT_ID=your_veryfi_client_id
VERYFI_CLIENT_SECRET=your_veryfi_client_secret
VERYFI_USERNAME=your_veryfi_username
VERYFI_API_KEY=your_veryfi_api_key

# Cloudflare R2 (for PDF storage)
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=your_bucket_name
R2_PUBLIC_URL=https://your-public-r2-url.r2.dev

# Google Gemini (for AI Copilot)
GEMINI_API_KEY=your_gemini_api_key

# JWT Secret (generate a random string)
JWT_SECRET=your_random_secret_key_here
```

#### 2.4 Initialize Database

```bash
# Run the SQL schema from database_schema.sql in your PostgreSQL client
# Or use psql:
psql -U user -d dbname -f ../database_schema.sql
```

### Step 3: Frontend Setup

#### 3.1 Install Dependencies

```bash
cd frontend
npm install
```

#### 3.2 Configure Environment Variables

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8001
```

---

## ▶️ Running the Application

### Terminal 1: Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

Backend will be available at: **http://localhost:8001**

API Documentation (Swagger): **http://localhost:8001/docs**

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:5173** (or next available port)

### Access the Application

1. Open **http://localhost:5173** in your browser
2. Login with test credentials:
   - Email: `super@admin.com` (or `client@acme.com` or `forwarder@dhl.com`)
   - Password: `password123`

---

## 👥 User Roles & Permissions

### 1. Super Admin
- View all companies and users
- Create new companies
- Manage all data across tenants
- Access all features

### 2. Client Admin
- Manage own company's charge master
- View all quotes sent to their company
- Accept/reject quotes
- Upload and analyze invoices
- Correct charge mappings
- Use AI Copilot
- View dashboard

### 3. Client User
- View quotes sent to their company
- View and analyze invoices
- Use AI Copilot (read-only)
- View dashboard

### 4. Forwarder Admin
- Submit quotes to clients
- Upload invoices for accepted quotes
- Manage own company's users
- View tracking

### 5. Forwarder User
- Submit quotes to clients
- Upload invoices for accepted quotes
- View tracking

---

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` — Login with email/password
- `POST /api/v1/auth/logout` — Logout
- `GET /api/v1/auth/me` — Get current user profile

### Quotes
- `GET /api/v1/quotes` — List quotes (filtered by role)
- `POST /api/v1/quotes` — Submit new quote (forwarder only)
- `GET /api/v1/quotes/{id}` — Get quote details
- `PATCH /api/v1/quotes/{id}/status` — Accept/reject quote (client only)
- `PATCH /api/v1/quotes/charges/{charge_id}/mapping` — Correct charge mapping

### Invoices
- `GET /api/v1/invoices` — List invoices
- `POST /api/v1/invoices/upload` — Upload invoice PDF
- `GET /api/v1/invoices/{id}` — Get invoice details
- `POST /api/v1/invoices/{id}/analyze` — Run anomaly analysis
- `GET /api/v1/invoices/{id}/anomalies` — Get detected anomalies
- `PATCH /api/v1/invoices/charges/{charge_id}/mapping` — Correct charge mapping

### Charge Master
- `GET /api/v1/charges` — List charges for user's company
- `POST /api/v1/charges` — Create new charge
- `PATCH /api/v1/charges/{id}` — Update charge
- `DELETE /api/v1/charges/{id}` — Soft delete charge
- `POST /api/v1/charges/{id}/aliases` — Add charge alias
- `DELETE /api/v1/charges/{id}/aliases/{alias_id}` — Remove alias

### Master Data
- `GET /api/v1/masters/airports` — List airports
- `GET /api/v1/masters/currencies` — List currencies

### AI Copilot
- `POST /api/v1/copilot/query` — Ask natural language question

### Dashboard
- `GET /api/v1/dashboard/stats` — Get dashboard statistics

### Tracking
- `GET /api/v1/tracking` — List shipments
- `GET /api/v1/tracking/{quote_id}/events` — Get tracking events
- `POST /api/v1/tracking/{quote_id}/events` — Add tracking event

### Companies
- `GET /api/v1/companies` — List companies (filtered by role)
- `POST /api/v1/companies` — Create company (super admin only)
- `PATCH /api/v1/companies/{id}/status` — Update company status

---

## 🗄 Database Schema

### Core Tables

**companies** — Multi-tenant company records
- `id`, `name`, `short_name`, `type` (client/forwarder), `is_active`

**profiles** — User accounts
- `id`, `email`, `name`, `password_hash`, `role`, `company_id`, `is_admin`, `is_active`

**charges** — Charge master (per company)
- `id`, `company_id`, `name`, `short_name`, `is_active`

**charge_aliases** — Charge name variations
- `id`, `charge_id`, `alias`

**quotes** — Quote headers
- `id`, `quote_ref`, `status`, `forwarder_id`, `buyer_id`, `tracking_number`, `gross_weight`, `volumetric_weight`, `chargeable_weight`, `currency_id`

**quote_charges** — Quote line items
- `id`, `quote_id`, `raw_charge_name`, `mapped_charge_id`, `rate`, `basis`, `qty`, `amount`, `mapping_tier`, `low_confidence`

**invoices** — Invoice headers
- `id`, `quote_id`, `invoice_number`, `invoice_date`, `file_path`

**invoice_charges** — Invoice line items
- `id`, `invoice_id`, `raw_charge_name`, `mapped_charge_id`, `rate`, `basis`, `qty`, `amount`, `mapping_tier`, `low_confidence`

**anomalies** — Detected discrepancies
- `id`, `invoice_id`, `invoice_charge_id`, `flag_type`, `description`, `variance`

**tracking_events** — Shipment tracking
- `id`, `quote_id`, `event_type`, `status`, `timestamp`

### Master Data Tables

**airports** — IATA codes
**currencies** — ISO currency codes
**countries** — Country names

---

## 🔧 Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'langchain_google_genai'`

**Solution**:
```bash
source .venv/bin/activate
pip install langchain-google-genai
```

**Error**: `GEMINI_API_KEY is not set`

**Solution**: Ensure `backend/.env` has `GEMINI_API_KEY=your_key` (no spaces around `=`)

### Database Connection Failed

**Error**: `could not connect to server`

**Solution**:
1. Verify `DATABASE_URL` in `backend/.env` is correct
2. Check Neon dashboard for connection string
3. Ensure database is running and accessible

### Frontend Can't Connect to Backend

**Error**: Network error when logging in

**Solution**:
1. Verify backend is running on port 8001
2. Check `frontend/.env` has `VITE_API_URL=http://localhost:8001`
3. Check CORS is enabled in backend (it is by default)

### Veryfi PDF Extraction Not Working

**Error**: `EXTRACTION_FAILED`

**Solution**:
1. Verify Veryfi credentials in `backend/.env`
2. Check Veryfi API quota (free tier: 100 docs/month)
3. Ensure PDF is valid and not corrupted

### Cloudflare R2 Upload Fails

**Error**: `STORAGE_FAILED`

**Solution**:
1. Verify R2 credentials in `backend/.env`
2. Check R2 bucket exists and is accessible
3. Verify R2_PUBLIC_URL is correct

### Copilot Returns "Not Configured"

**Error**: `Copilot is not configured yet`

**Solution**:
1. Add `GEMINI_API_KEY` to `backend/.env`
2. Restart backend: `uvicorn app.main:app --reload --port 8001`
3. Ensure no spaces around `=` in `.env`

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8001/docs (Swagger UI)
- **Database Schema**: See `database_schema.sql`
- **Requirements Document**: See `.kiro/specs/backend-rebuild/requirements.md`
- **Frontend API Contract**: See `frontend/API_CONTRACT.md`

---

## 📝 License

This project is proprietary. All rights reserved.

---

## 🤝 Support

For issues or questions, refer to the troubleshooting section above or check the API documentation at `/docs`.

---

**Last Updated**: June 2026  
**Version**: 1.0.0  
**Status**: Production Ready
