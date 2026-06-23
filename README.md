# LogiSight — Freight Audit Platform

LogiSight is a full-stack freight audit platform built for logistics companies to manage quotes, invoices, charge mappings, anomaly detection, and AI-powered analytics. It connects freight forwarders with their clients in a multi-tenant environment with strict data isolation.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [User Roles & Permissions](#user-roles--permissions)
5. [Features](#features)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Setup & Running](#setup--running)
9. [Environment Variables](#environment-variables)
10. [Test Accounts](#test-accounts)
11. [Folder Structure](#folder-structure)
12. [Charge Mapping System](#charge-mapping-system)
13. [AI Copilot](#ai-copilot)
14. [Anomaly Detection Logic](#anomaly-detection-logic)

---

## What It Does

LogiSight solves a core pain point in logistics: freight forwarders send invoices that don't always match the quotes they submitted. Clients have to manually cross-reference every line item to catch overcharges, missing charges, or rate changes.

LogiSight automates this:

- Forwarders submit quotes with itemized charges
- Clients review and accept/reject quotes
- Forwarders upload PDF invoices for accepted quotes — charges are extracted automatically via OCR
- Every charge gets mapped to the client's standardized charge master (dictionary-based, self-learning)
- One click runs a full variance analysis: charge-by-charge comparison, net variance, and flagged anomalies
- An AI Copilot lets clients ask natural language questions about their freight data

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Framework | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.0 (async) |
| Database Driver | asyncpg |
| Authentication | JWT (HS256) via `python-jose` |
| Password Hashing | bcrypt via `passlib` |
| PDF OCR | Veryfi API |
| File Storage | Cloudflare R2 (S3-compatible) via `boto3` |
| AI / LLM | Google Gemini 2.5 Flash via `langchain-google-genai` |
| Server | Uvicorn (ASGI) |
| Validation | Pydantic v2 |
| Settings | pydantic-settings |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 5 |
| Routing | React Router 7 |
| Data Fetching | TanStack Query (React Query) v5 |
| HTTP Client | Axios |
| Forms | React Hook Form + Zod |
| Styling | Tailwind CSS 3 |
| Icons | Lucide React |

### Infrastructure
| Component | Service |
|---|---|
| Database | Neon PostgreSQL (serverless) |
| File Storage | Cloudflare R2 |
| Invoice Extraction | Veryfi API |
| AI Copilot | Google Gemini 2.5 Flash |


---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│              React + TypeScript (Vite)                      │
│                  http://localhost:5173                       │
└──────────────────────┬──────────────────────────────────────┘
                       │  HTTP/REST (JWT in Authorization header)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│                  http://localhost:8001                       │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  auth    │  │  quotes  │  │ invoices │  │ charges  │   │
│  │  users   │  │ tracking │  │ copilot  │  │dashboard │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                       │                                     │
│               SQLAlchemy (async)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼──────────────┐
          ▼            ▼              ▼
   ┌────────────┐ ┌─────────┐ ┌──────────────┐
   │  Neon      │ │Cloudflare│ │  Google      │
   │ PostgreSQL │ │   R2    │ │  Gemini API  │
   │(serverless)│ │(PDF files│ │  (Copilot)   │
   └────────────┘ └─────────┘ └──────────────┘
                       ▲
                  ┌─────────┐
                  │ Veryfi  │
                  │  API    │
                  │ (OCR)   │
                  └─────────┘
```

All routes are prefixed `/api/v1`. CORS is enabled for `localhost:5173`, `5174`, `5175`, `3000`.


---

## User Roles & Permissions

There are 5 roles in the system. Every user belongs to a company, and data is strictly isolated per company.

| Role | Type | What they can do |
|---|---|---|
| `super_admin` | Platform | Full access to everything, all companies |
| `client` (admin) | Client company | Manage charge master, accept/reject quotes, analyze invoices, use copilot |
| `client` (user) | Client company | View quotes and invoices, run analysis |
| `forwarder` (admin) | Forwarder company | Submit quotes, upload invoices, manage team |
| `forwarder` (user) | Forwarder company | Submit quotes, upload invoices |

### Access Matrix

| Feature | Super Admin | Client Admin | Client User | Forwarder Admin | Forwarder User |
|---|:---:|:---:|:---:|:---:|:---:|
| View quotes | ✅ All | ✅ Own | ✅ Own | ✅ Own | ✅ Own |
| Submit quotes | ✅ | ❌ | ❌ | ✅ | ✅ |
| Accept/Reject quotes | ✅ | ✅ | ✅ | ❌ | ❌ |
| Upload invoices | ✅ | ❌ | ❌ | ✅ | ✅ |
| Analyze invoices | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage charge master | ✅ | ✅ | ❌ | ❌ | ❌ |
| Use AI copilot | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage companies | ✅ | ❌ | ❌ | ❌ | ❌ |
| View tracking | ✅ | ✅ | ✅ | ✅ | ✅ |


---

## Features

### 1. Authentication & Authorization
- Email/password login returning a JWT token (7-day expiry)
- Token stored in `localStorage`, sent as `Authorization: Bearer <token>` on every request
- `GET /api/v1/auth/me` — returns full user profile with role and company info
- Stateless logout (client drops the token)
- Every protected route validates the JWT and enforces role-based access
- Multi-tenant isolation: all queries are automatically scoped to the user's `company_id`

### 2. Charge Master Management
- Each client company maintains its own standardized charge dictionary
- Charges have a `name`, `short_name`, and a list of `aliases`
- Aliases are alternate names for the same charge (e.g., "Fuel Surcharge", "FSC", "Fuel Levy")
- Only client admins can create, edit, or deactivate charges
- Soft deletes via `is_active` flag — deactivated charges won't be matched during mapping
- Duplicate names and short names are prevented within the same company

### 3. Quote Management
- Forwarders submit quotes with full shipment details:
  - Origin/destination airports (IATA codes), tracking number, weights (gross, volumetric, chargeable)
  - Currency, sender/receiver info
  - Multiple itemized charge lines (name, rate, basis, quantity, amount)
- Quote reference is auto-generated (`QR-<timestamp>`)
- Each charge is immediately run through the charge mapping pipeline (see below)
- Clients can list all quotes for their company, view full details, and accept or reject
- Rejected quotes can include a rejection note
- Only `ACCEPTED` quotes can have invoices uploaded against them

### 4. Invoice Management
- Forwarders upload a PDF invoice linked to an accepted quote by tracking number
- PDF is processed through two pipelines in sequence:
  1. **Veryfi OCR** — extracts `invoice_number`, `invoice_date`, and all line items
  2. **Cloudflare R2 upload** — stores the PDF and returns a permanent public URL
- Extracted charges are run through the same charge mapping pipeline as quotes
- Clients can view invoices with all extracted line items, mapped charge names, and the original PDF
- The PDF is shown as a downloadable strip at the bottom of the invoice detail page
- File size limit: 10 MB

### 5. Variance Analysis & Anomaly Detection
- Available to clients only, triggered by clicking "Analyse Invoice"
- Compares invoice charges vs. quote charges line-by-line using `mapped_charge_id` as the common key
- Re-runnable: clears old anomalies and re-runs fresh on each click
- Detects 6 anomaly types (see [Anomaly Detection Logic](#anomaly-detection-logic))
- Shows per-charge variance (invoice amount − quote amount) in the charge table
- Shows net total variance in the summary footer

### 6. AI Copilot (Text-to-SQL)
- Natural language interface over the user's freight data
- Powered by Google Gemini 2.5 Flash via LangChain
- Multi-tenant: queries are automatically scoped to the user's company
- Built-in guardrails: only read-only SELECT queries allowed
- 8-second query timeout, 200-row cap on results
- Returns a plain-English summary of results, not raw SQL or JSON
- Available to clients and super admin only

### 7. Shipment Tracking
- Lists all shipments (quotes) with their latest tracking status
- Shows origin, destination, forwarder, buyer, and last event time
- Per-shipment event timeline with location, status, and description
- Filtered by company: forwarders see their shipments, clients see their received shipments

### 8. Dashboard
- Role-specific KPI cards on login:
  - Open quotes (SUBMITTED status)
  - Accepted quotes (total)
  - Invoices uploaded
  - Anomalies pending

### 9. Company & User Management (Super Admin)
- Super admin can create new companies (client or forwarder type)
- Company creation simultaneously creates an admin user for that company
- Super admin can activate/deactivate companies
- Company admins can add users to their own company

### 10. Master Data
- Pre-seeded airports (with IATA codes), currencies, and countries
- Available as dropdown data when submitting quotes
- Managed at platform level, not per-company


---

## Database Schema

The database has 12 tables across 5 logical groups. All relationships are enforced with foreign keys.

### Tables Overview

```
companies          ← core tenant unit (type: client | forwarder)
profiles           ← users, linked to a company
countries          ← master data
currencies         ← master data
airports           ← master data (has country_id FK)
charges            ← charge master, scoped per company
charge_aliases     ← alternate names for charges
quotes             ← quote headers (forwarder → buyer)
quote_charges      ← line items for a quote
invoices           ← invoice headers, linked to a quote
invoice_charges    ← line items extracted from invoice PDF
anomalies          ← detected discrepancies per invoice
tracking_events    ← shipment status events, linked to a quote
audit_logs         ← user action log
```

### Table Details

#### `companies`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| name | VARCHAR(255) UNIQUE | |
| short_name | VARCHAR(50) UNIQUE | |
| type | VARCHAR(20) | `client` or `forwarder` |
| address_line1 | TEXT | |
| city | VARCHAR(100) | |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMP | |

#### `profiles`
| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(255) PK | UUID string |
| email | VARCHAR(255) UNIQUE | |
| name | VARCHAR(255) | |
| password_hash | VARCHAR(255) | bcrypt |
| role | VARCHAR(20) | `client`, `forwarder`, `super_admin` |
| company_id | INT FK → companies | nullable for super_admin |
| is_admin | BOOLEAN | company admin flag |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |

#### `airports`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| name | VARCHAR(255) | |
| iata_code | VARCHAR(3) UNIQUE | e.g. `DEL`, `SIN` |
| country_id | INT FK → countries | |
| is_active | BOOLEAN | |

#### `currencies`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| name | VARCHAR(100) UNIQUE | e.g. `US Dollar` |
| short_name | VARCHAR(10) UNIQUE | e.g. `USD` |
| is_active | BOOLEAN | |

#### `charges`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| company_id | INT FK → companies | tenant-scoped |
| name | VARCHAR(255) | unique per company |
| short_name | VARCHAR(50) | unique per company |
| is_active | BOOLEAN | |
| created_at / updated_at | TIMESTAMP | |

#### `charge_aliases`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| charge_id | INT FK → charges | cascade delete |
| alias | VARCHAR(255) | unique per charge |

#### `quotes`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| quote_ref | VARCHAR(50) UNIQUE | auto-generated `QR-<ts>` |
| status | VARCHAR(20) | `SUBMITTED`, `ACCEPTED`, `REJECTED` |
| rejection_note | TEXT | |
| forwarder_id | INT FK → companies | |
| buyer_id | INT FK → companies | must differ from forwarder_id |
| origin_airport_id | INT FK → airports | |
| destination_airport_id | INT FK → airports | |
| tracking_number | VARCHAR(100) | |
| gross_weight | NUMERIC(10,2) | |
| volumetric_weight | NUMERIC(10,2) | |
| chargeable_weight | NUMERIC(10,2) | max(gross, volumetric) |
| currency_id | INT FK → currencies | |
| created_at | TIMESTAMP | |

#### `quote_charges`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| quote_id | INT FK → quotes | cascade delete |
| raw_charge_name | VARCHAR(255) | as entered by forwarder |
| mapped_charge_id | INT FK → charges | nullable if unmapped |
| mapped_charge_name | VARCHAR(255) | denormalized for speed |
| similarity_score | NUMERIC(5,4) | 0.0–1.0 |
| mapping_tier | VARCHAR(20) | `DICTIONARY`, `HUMAN`, `UNMAPPED` |
| low_confidence | BOOLEAN | |
| rate | NUMERIC(10,2) | |
| basis | VARCHAR(50) | `Per KG`, `Per Shipment`, `Per CBM` |
| qty | NUMERIC(10,2) | |
| amount | NUMERIC(10,2) | |


#### `invoices`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| quote_id | INT FK → quotes | cascade delete |
| invoice_number | VARCHAR(100) UNIQUE | from Veryfi extraction |
| invoice_date | DATE | from Veryfi extraction |
| file_path | TEXT | public URL from Cloudflare R2 |
| uploaded_at | TIMESTAMP | |

#### `invoice_charges`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| invoice_id | INT FK → invoices | cascade delete |
| raw_charge_name | VARCHAR(255) | as extracted by Veryfi |
| mapped_charge_id | INT FK → charges | nullable |
| mapped_charge_name | VARCHAR(255) | |
| similarity_score | NUMERIC(5,4) | |
| mapping_tier | VARCHAR(20) | |
| low_confidence | BOOLEAN | |
| rate | NUMERIC(10,2) | |
| basis | VARCHAR(50) | |
| qty | NUMERIC(10,2) | |
| amount | NUMERIC(10,2) | |

#### `anomalies`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| invoice_id | INT FK → invoices | cascade delete |
| invoice_charge_id | INT FK → invoice_charges | nullable (SET NULL) |
| flag_type | VARCHAR(30) | see anomaly types below |
| description | TEXT | human-readable explanation |
| variance | NUMERIC(10,2) | invoice − quote amount |
| created_at | TIMESTAMP | |

#### `tracking_events`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| quote_id | INT FK → quotes | cascade delete |
| event_time | TIMESTAMP | |
| location | VARCHAR(255) | |
| status | VARCHAR(100) | |
| description | TEXT | |

### Entity Relationships

```
companies ──< profiles
companies ──< charges ──< charge_aliases
companies ──< quotes (as forwarder)
companies ──< quotes (as buyer)
airports  ──< quotes (origin)
airports  ──< quotes (destination)
currencies──< quotes
quotes    ──< quote_charges ──> charges
quotes    ──< invoices ──< invoice_charges ──> charges
                       ──< anomalies ──> invoice_charges
quotes    ──< tracking_events
countries ──< airports
```


---

## API Reference

All endpoints are prefixed with `/api/v1`. All requests (except `/health`) require:
```
Authorization: Bearer <jwt_token>
```

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | None | Login with email/password, returns JWT token |
| POST | `/auth/logout` | Required | Stateless logout (204 No Content) |
| GET | `/auth/me` | Required | Returns current user profile |

**POST `/auth/login`**
```json
// Request
{ "email": "user@example.com", "password": "password123" }

// Response 200
{
  "token": "eyJ...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "role": "client",
    "company_id": 1,
    "company_type": "client",
    "company_name": "Acme Corp",
    "is_admin": true
  }
}
```

---

### Quotes

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/quotes` | All | List quotes (filtered by role) |
| POST | `/quotes` | forwarder, super_admin | Submit new quote |
| GET | `/quotes/{id}` | All | Get quote with all charges |
| PATCH | `/quotes/{id}/status` | client, super_admin | Accept or reject a quote |
| PATCH | `/quotes/charges/{charge_id}/mapping` | client, super_admin | Correct a charge mapping |

**POST `/quotes`** (forwarder only)
```json
{
  "buyer_id": 1,
  "origin_airport_id": 3,
  "destination_airport_id": 7,
  "tracking_number": "TRK-001",
  "gross_weight": 500.0,
  "volumetric_weight": 450.0,
  "chargeable_weight": 500.0,
  "currency_id": 1,
  "charges": [
    { "raw_charge_name": "Freight Charge", "rate": 5.0, "basis": "Per KG", "qty": 500, "amount": 2500.0 },
    { "raw_charge_name": "Fuel Surcharge", "rate": 200.0, "basis": "Per Shipment", "qty": 1, "amount": 200.0 }
  ]
}
```

**PATCH `/quotes/{id}/status`**
```json
{ "status": "ACCEPTED" }
// or
{ "status": "REJECTED", "rejection_note": "Rate too high" }
```

**PATCH `/quotes/charges/{charge_id}/mapping`** — self-learning, auto-adds alias
```json
{ "mapped_charge_id": 5 }
```

---

### Invoices

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/invoices` | All | List invoices (filtered by role) |
| GET | `/invoices/{id}` | All | Get invoice with all extracted charges |
| POST | `/invoices/upload` | forwarder, super_admin | Upload PDF invoice (multipart/form-data) |
| PATCH | `/invoices/charges/{charge_id}/mapping` | client, super_admin | Correct invoice charge mapping |
| POST | `/invoices/{id}/analyze` | client, super_admin | Run variance & anomaly analysis |
| GET | `/invoices/{id}/anomalies` | client, super_admin | Get stored anomalies |

**POST `/invoices/upload`** — multipart/form-data
```
tracking_number: "TRK-001"
file: <PDF binary>
```

**POST `/invoices/{id}/analyze`** — returns list of anomalies
```json
[
  {
    "id": 1,
    "invoice_id": 12,
    "invoice_charge_id": 34,
    "flag_type": "AMOUNT_MISMATCH",
    "description": "'Freight Charge': amount changed from 2500.0 (quote) to 2750.0 (invoice)",
    "variance": 250.0
  }
]
```


---

### Charges (Charge Master)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/charges` | client, super_admin | List all charges for company (with aliases) |
| POST | `/charges` | client admin, super_admin | Create new charge |
| PATCH | `/charges/{id}` | client admin, super_admin | Update charge name/short_name/active |
| POST | `/charges/{id}/aliases` | client admin, super_admin | Add alias to a charge |
| DELETE | `/charges/aliases/{alias_id}` | client admin, super_admin | Remove alias |

**GET `/charges`** response
```json
[
  {
    "id": 1,
    "company_id": 2,
    "name": "Freight Charge",
    "short_name": "FC",
    "is_active": true,
    "aliases": [
      { "id": 1, "charge_id": 1, "alias": "Air Freight" },
      { "id": 2, "charge_id": 1, "alias": "Freight" }
    ]
  }
]
```

---

### Companies

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/companies` | All | List companies (role-filtered) |
| POST | `/companies` | super_admin | Create company + admin user |
| PATCH | `/companies/{id}/status` | super_admin | Activate/deactivate company |

Note on `GET /companies` role filtering:
- **forwarder** sees only client companies (to pick "addressed to" when submitting quotes)
- **client** sees only forwarder companies
- **super_admin** sees all

**POST `/companies`** (super_admin only)
```json
{
  "name": "New Logistics Co",
  "short_name": "NLC",
  "type": "forwarder",
  "address": "123 Freight Lane",
  "city": "Singapore",
  "admin_email": "admin@nlc.com",
  "admin_name": "Admin User",
  "admin_password": "securepass123"
}
```

---

### Users

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/users` | All (company-scoped) | List users in own company |
| POST | `/users` | company admin | Create user in own company |

---

### Dashboard

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/dashboard/stats` | All | KPI stats for current user's company |

```json
{
  "open_quotes": 5,
  "anomalies_pending": 0,
  "invoices_this_month": 12,
  "total_accepted": 34
}
```

---

### Tracking

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/tracking` | All | List all shipments with latest status |
| GET | `/tracking/{quote_id}/events` | All | Get event timeline for a shipment |

---

### Masters (Dropdown Data)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/masters/airports` | All | List active airports with IATA codes |
| GET | `/masters/currencies` | All | List active currencies |

---

### AI Copilot

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/copilot/query` | client, super_admin | Ask a natural language question |

```json
// Request
{ "question": "Which forwarder had the most anomalies this month?" }

// Response
{ "answer": "DHL Express had the most anomalies this month with 7 flagged invoices..." }
```

---

### Health Check

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Returns `{"status": "ok"}` |


---

## Setup & Running

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Neon PostgreSQL database (or any PostgreSQL 14+)
- A Veryfi account (free: 100 docs/month)
- A Cloudflare R2 bucket (free tier)
- A Google Gemini API key (for AI Copilot)

---

### 1. Clone & set up backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Create `backend/.env` (see [Environment Variables](#environment-variables) below).

Run database migrations to create all tables:
```bash
# If tables don't exist yet, run the schema SQL against your Neon DB
# using the Neon console or psql
```

Seed initial data (airports, currencies, countries, test users):
```bash
# Run database_schema.sql in your Neon console SQL editor
```

Start the backend:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Backend is now running at **http://localhost:8001**
Swagger docs at **http://localhost:8001/api/v1/openapi.json**

---

### 2. Set up frontend

```bash
cd frontend

# Install dependencies
npm install
```

Create `frontend/.env`:
```bash
VITE_API_URL=http://localhost:8001
```

Start the dev server:
```bash
npm run dev
```

Frontend is now running at **http://localhost:5173**

---

### 3. Run both (production build)

```bash
# Build frontend
cd frontend && npm run build

# Start backend (serves everything)
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8001
```


---

## Environment Variables

### Backend (`backend/.env`)

```env
# Database (Neon PostgreSQL — note: no spaces around = sign)
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname

# JWT Auth
JWT_SECRET=your-random-secret-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Veryfi OCR (https://app.veryfi.com)
VERYFI_CLIENT_ID=your_client_id
VERYFI_CLIENT_SECRET=your_client_secret
VERYFI_USERNAME=your_username
VERYFI_API_KEY=your_api_key

# Cloudflare R2 Storage
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key
R2_BUCKET_NAME=logisight-invoices
R2_PUBLIC_URL=https://pub-<hash>.r2.dev

# Google Gemini (for AI Copilot)
GEMINI_API_KEY=your_gemini_api_key
```

> **Important**: No spaces around `=` in .env files. `KEY=value` is correct. `KEY = value` will not be parsed by pydantic-settings.

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8001
```

---

## Test Accounts

All test accounts use the password: **`password123`**

| Email | Role | Company |
|---|---|---|
| `super@admin.com` | super_admin | — (platform level) |
| `client@acme.com` | client (admin) | Acme Corp |
| `forwarder@dhl.com` | forwarder (admin) | DHL Express |

These accounts are seeded in `database_schema.sql`.


---

## Folder Structure

```
LogiSight/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py          # Login, logout, /me
│   │   │       ├── charges.py       # Charge master CRUD + aliases
│   │   │       ├── companies.py     # Company management (super admin)
│   │   │       ├── copilot.py       # AI Copilot endpoint
│   │   │       ├── dashboard.py     # KPI stats
│   │   │       ├── invoices.py      # Upload, extract, analyze
│   │   │       ├── masters.py       # Airports, currencies
│   │   │       ├── quotes.py        # Quote lifecycle
│   │   │       ├── tracking.py      # Shipment tracking
│   │   │       └── users.py         # User management
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings (reads .env)
│   │   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   │   ├── dependencies.py      # get_current_user, require_roles
│   │   │   └── security.py          # JWT create/verify, bcrypt hash
│   │   ├── models/
│   │   │   ├── base.py              # SQLAlchemy declarative base
│   │   │   ├── company.py           # Company model
│   │   │   ├── invoice.py           # Invoice, InvoiceCharge, Anomaly
│   │   │   ├── master.py            # Airport, Currency, Country, Charge, ChargeAlias
│   │   │   ├── quote.py             # Quote, QuoteCharge
│   │   │   ├── tracking.py          # TrackingEvent, AuditLog
│   │   │   └── user.py              # Profile (user)
│   │   ├── services/
│   │   │   ├── copilot.py           # LangChain orchestration (NL→SQL→summary)
│   │   │   ├── copilot_executor.py  # Safe SQL execution with timeout + row cap
│   │   │   ├── copilot_guardrail.py # SQL validation (read-only enforcement)
│   │   │   ├── copilot_schema.py    # Schema context string for LLM prompt
│   │   │   ├── r2_storage.py        # Cloudflare R2 upload via boto3
│   │   │   └── veryfi_client.py     # Veryfi API PDF extraction
│   │   └── main.py                  # FastAPI app, CORS, route registration
│   ├── requirements.txt
│   └── .env                         # Credentials (gitignored)
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts            # All API call functions (axios)
│   │   │   └── types.ts             # TypeScript interfaces for all models
│   │   ├── components/              # Reusable UI components
│   │   ├── hooks/
│   │   │   └── useAuth.ts           # Auth state, login/logout, JWT storage
│   │   ├── pages/                   # One file per page/route
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Quotes.tsx
│   │   │   ├── QuoteDetail.tsx
│   │   │   ├── CreateQuote.tsx
│   │   │   ├── Invoices.tsx
│   │   │   ├── InvoiceAnalysis.tsx  # Main analysis page with variance + anomalies
│   │   │   ├── ChargeMaster.tsx
│   │   │   ├── Tracking.tsx
│   │   │   ├── Copilot.tsx
│   │   │   ├── Companies.tsx
│   │   │   └── Users.tsx
│   │   └── main.tsx
│   ├── .env                         # VITE_API_URL
│   └── package.json
│
├── database_schema.sql              # Complete PostgreSQL schema + seed data
├── README.md                        # This file
└── DATABASE_DESIGN.md               # ERD and extended schema docs
```


---

## Charge Mapping System

This is the core intelligence of LogiSight. Forwarders and carriers use inconsistent names for the same charges (e.g., "Fuel Levy", "FSC", "Fuel Surcharge", "Fuel Surcharge Per Chg Wt" are all the same thing). The mapping system normalizes these automatically.

### How It Works

Every charge name that comes in (from a quote submission or invoice extraction) runs through a 4-step dictionary pipeline:

```
Input: "FSC"
         │
         ▼
Step 1: Exact match on charge.name         → "Fuel Surcharge"? → hit → DICTIONARY (score: 1.0)
         │ miss
         ▼
Step 2: Exact match on charge.short_name   → "FSC"? → hit → DICTIONARY (score: 1.0)
         │ miss
         ▼
Step 3: Exact match on charge_aliases      → any alias = "FSC"? → hit → DICTIONARY (score: 0.95)
         │ miss
         ▼
Step 4: Partial / contains match on name   → name contains "fsc"? → hit → DICTIONARY (score: 0.75, low_confidence: true)
         │ miss
         ▼
         UNMAPPED (mapped_charge_id: null, low_confidence: true)
```

All matching is **case-insensitive**.

### Self-Learning

When a client manually corrects a mapping (by picking the right charge from the dropdown), the system automatically adds the raw charge name as an alias to that charge:

```
Human says: "FSC" → "Fuel Surcharge"
System adds: charge_aliases(charge_id=5, alias="FSC")
Next time: "FSC" → auto-matches → DICTIONARY tier
```

This means the system gets smarter every time a human corrects it — corrections never need to be made twice.

### Mapping Tiers

| Tier | Meaning | Confidence |
|---|---|---|
| `DICTIONARY` | Matched via name, short_name, or alias | High (0.75–1.0) |
| `HUMAN` | Manually corrected by client | Highest (1.0) |
| `UNMAPPED` | No match found | None |

Note: Vector/embedding-based matching and LLM fallback are reserved for future enhancement. The current system uses pure dictionary lookup only.

---

## AI Copilot

The Copilot feature lets clients ask natural language questions about their freight data without writing SQL.

### Pipeline

```
User types: "Which forwarder had the most anomalies this month?"
                              │
                              ▼
                    Build system prompt:
                    - Full DB schema context
                    - Mandatory tenant filter (buyer_id = X)
                    - Security rules (SELECT only, no password_hash, etc.)
                              │
                              ▼
                 Google Gemini 2.5 Flash
                 generates PostgreSQL SELECT
                              │
                              ▼
                    Guardrail validation:
                    - Must be SELECT/WITH
                    - No DML keywords
                    - No restricted tables/columns
                              │
                         fail → "I can only answer read-only questions"
                              │ pass
                              ▼
                    Execute with safeties:
                    - 8-second timeout
                    - 200-row hard cap
                              │
                              ▼
                 Gemini summarizes rows → plain English
                              │
                              ▼
            "DHL Express had the most anomalies with 7 flagged invoices,
             totalling a variance of $1,240 above quoted amounts."
```

### Security

- Multi-tenant: the LLM prompt includes a mandatory `WHERE buyer_id = X` clause
- The guardrail rejects any query containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `password_hash`, or any non-whitelisted table
- Even if the LLM goes rogue, the SQL executor only runs in a read-only context


---

## Anomaly Detection Logic

When a client clicks "Analyse Invoice", the backend runs a full comparison of the invoice against its linked quote.

### Detection Process

```python
# Build lookup: quote charges keyed by mapped_charge_id
quote_map = { qc.mapped_charge_id: qc for qc in quote_charges }

for each invoice_charge:
    if invoice_charge.mapped_charge_id is None:
        → UNEXPECTED_CHARGE  (couldn't be mapped at all)
    elif invoice_charge.mapped_charge_id not in quote_map:
        → UNEXPECTED_CHARGE  (mapped but not in the original quote)
    else:
        qc = quote_map[invoice_charge.mapped_charge_id]
        if invoice_charge.basis != qc.basis:
            → BASIS_MISMATCH
        if invoice_charge.rate != qc.rate:
            → RATE_MISMATCH   (variance = inv_rate - quote_rate)
        if invoice_charge.amount != qc.amount:
            → AMOUNT_MISMATCH (variance = inv_amount - quote_amount)

for each quote_charge with a mapping:
    if quote_charge.mapped_charge_id not matched by any invoice charge:
        → MISSING_CHARGE     (variance = -quote_amount, negative = undercharged)

if other invoices exist for same quote:
    → DUPLICATE_INVOICE
```

### Anomaly Types

| Flag Type | What it means | Variance |
|---|---|---|
| `AMOUNT_MISMATCH` | Invoice amount ≠ quote amount for the same charge | invoice − quote |
| `RATE_MISMATCH` | Rate changed between quote and invoice | inv_rate − quote_rate |
| `BASIS_MISMATCH` | Billing basis changed (e.g., Per KG → Per Shipment) | null |
| `UNEXPECTED_CHARGE` | Charge in invoice not present in the quote | invoice amount |
| `MISSING_CHARGE` | Charge in quote is absent from the invoice | negative quote amount |
| `DUPLICATE_INVOICE` | Another invoice already exists for the same quote | null |

### Re-runnable

Analysis always clears all previous anomalies for that invoice before running. This means you can correct charge mappings and re-run to get an updated analysis with no stale results.

---

## Error Responses

All errors return a consistent structure:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Common codes:
| Code | HTTP Status | Meaning |
|---|---|---|
| `UNAUTHORIZED` | 401 | Invalid credentials or missing token |
| `FORBIDDEN` | 403 | Valid token but insufficient role |
| `NOT_FOUND` | 404 | Resource doesn't exist or is not visible to user |
| `VALIDATION_ERROR` | 400 | Invalid input (bad field values, duplicates, etc.) |
| `EXTRACTION_FAILED` | 500 | Veryfi OCR failed |
| `STORAGE_FAILED` | 500 | Cloudflare R2 upload failed |

---

## Key Design Decisions

**Why dictionary matching instead of vector/ML?**
Dictionary matching is predictable, debuggable, and self-improving. Every human correction permanently improves future auto-mappings. ML approaches require training data and infrastructure that add complexity without clear benefit at this stage.

**Why Neon PostgreSQL?**
Serverless PostgreSQL with zero cold start on the free tier. No VMs to manage, scales automatically, works perfectly with asyncpg.

**Why Cloudflare R2?**
Zero egress fees for public file access. PDFs are stored once and read frequently — R2's pricing model is ideal.

**Why stateless JWT instead of sessions?**
Simplicity. No session store required. The 7-day token expiry is appropriate for a business application where users are expected to be on trusted devices.

**Why Gemini 2.5 Flash for the copilot?**
Fast inference, good SQL generation quality, generous free tier, and direct support via `langchain-google-genai`.

---

*LogiSight v1.0.0 — Built June 2026*
