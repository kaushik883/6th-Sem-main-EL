# Database Design Document

## Overview
Complete database schema for FreightAudit Pro supporting all features including quote management, invoice audit, anomaly detection, tracking, and AI copilot.

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────┐
│   COUNTRIES     │
│─────────────────│
│ id (PK)         │
│ name            │
│ short_name      │
│ is_active       │
└─────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────┐         ┌─────────────────┐
│   AIRPORTS      │         │   CURRENCIES    │
│─────────────────│         │─────────────────│
│ id (PK)         │         │ id (PK)         │
│ name            │         │ name            │
│ iata_code       │         │ short_name      │
│ country_id (FK) │         │ is_active       │
│ is_active       │         └─────────────────┘
└─────────────────┘                 │
        │                           │
        │                           │
        │                           │
┌─────────────────┐                 │
│   COMPANIES     │                 │
│─────────────────│                 │
│ id (PK)         │                 │
│ name            │                 │
│ short_name      │                 │
│ type            │◄────┐           │
│ address         │     │           │
│ city            │     │           │
│ country_id (FK) │     │           │
│ is_active       │     │           │
└─────────────────┘     │           │
        │               │           │
        │ 1:N           │           │
        ▼               │           │
┌─────────────────┐     │           │
│   PROFILES      │     │           │
│─────────────────│     │           │
│ id (PK)         │     │           │
│ email           │     │           │
│ name            │     │           │
│ password_hash   │     │           │
│ role            │     │           │
│ company_id (FK) │─────┘           │
│ is_admin        │                 │
│ is_active       │                 │
└─────────────────┘                 │
                                    │
┌─────────────────┐                 │
│    CHARGES      │                 │
│─────────────────│                 │
│ id (PK)         │                 │
│ company_id (FK) │─────┐           │
│ name            │     │           │
│ short_name      │     │           │
│ is_active       │     │           │
└─────────────────┘     │           │
        │               │           │
        │ 1:N           │           │
        ▼               │           │
┌─────────────────┐     │           │
│ CHARGE_ALIASES  │     │           │
│─────────────────│     │           │
│ id (PK)         │     │           │
│ charge_id (FK)  │     │           │
│ alias           │     │           │
└─────────────────┘     │           │
                        │           │
                        │           │
┌───────────────────────┼───────────┼───────────────────┐
│                       │           │                   │
│                  QUOTES                               │
│───────────────────────────────────────────────────────│
│ id (PK)                                               │
│ quote_ref                                             │
│ status (SUBMITTED/ACCEPTED/REJECTED)                  │
│ forwarder_id (FK) ────────────────────────────────────┤
│ buyer_id (FK) ────────────────────────────────────────┤
│ origin_airport_id (FK)                                │
│ destination_airport_id (FK)                           │
│ tracking_number                                       │
│ gross_weight, volumetric_weight, chargeable_weight    │
│ currency_id (FK) ─────────────────────────────────────┤
│ quote_date                                            │
└───────────────────────────────────────────────────────┘
        │                           │
        │ 1:N                       │ 1:N
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│ QUOTE_CHARGES   │         │ TRACKING_EVENTS │
│─────────────────│         │─────────────────│
│ id (PK)         │         │ id (PK)         │
│ quote_id (FK)   │         │ quote_id (FK)   │
│ raw_charge_name │         │ event_time      │
│ mapped_charge_id│◄────┐   │ location        │
│ rate, basis, qty│     │   │ status          │
│ amount          │     │   │ description     │
│ mapping_tier    │     │   └─────────────────┘
│ similarity_score│     │
└─────────────────┘     │
                        │
        │               │
        │ 1:N           │
        ▼               │
┌─────────────────┐     │
│   INVOICES      │     │
│─────────────────│     │
│ id (PK)         │     │
│ quote_id (FK)   │     │
│ invoice_number  │     │
│ invoice_date    │     │
│ file_path       │     │
└─────────────────┘     │
        │               │
        │ 1:N           │
        ▼               │
┌─────────────────┐     │
│ INVOICE_CHARGES │     │
│─────────────────│     │
│ id (PK)         │     │
│ invoice_id (FK) │     │
│ raw_charge_name │     │
│ mapped_charge_id│─────┘
│ rate, basis, qty│
│ amount          │
│ mapping_tier    │
│ similarity_score│
└─────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────┐
│   ANOMALIES     │
│─────────────────│
│ id (PK)         │
│ invoice_id (FK) │
│ invoice_charge  │
│ flag_type       │
│ description     │
│ variance        │
└─────────────────┘
```

---

## Table Descriptions

### 1. Core Tables

#### **companies**
- Stores both client and forwarder companies
- `type`: 'client' or 'forwarder'
- Soft delete via `is_active`

#### **profiles**
- User accounts linked to companies (except super_admin)
- `role`: 'super_admin', 'client', 'forwarder'
- `is_admin`: Company admin flag
- Password stored as bcrypt hash

### 2. Master Data

#### **countries**
- Reference data for countries
- Used by airports and companies

#### **currencies**
- Reference data for currencies
- Used in quotes

#### **airports**
- Airport master data with IATA codes
- Linked to countries

#### **charges**
- Company-specific charge master
- Each client company maintains their own charges
- Unique constraint: (company_id, name) and (company_id, short_name)

#### **charge_aliases**
- Alternative names for charges
- Used for fuzzy matching during charge mapping
- Example: "FSC" → "Fuel Surcharge"

### 3. Quote Module

#### **quotes**
- Freight quotes from forwarders to buyers
- Status workflow: SUBMITTED → ACCEPTED/REJECTED
- Contains shipment details (weights, airports, tracking)
- `chargeable_weight` auto-calculated as max(gross, volumetric)

#### **quote_charges**
- Line items for each quote
- `raw_charge_name`: Original name from forwarder
- `mapped_charge_id`: Mapped to buyer's charge master
- `mapping_tier`: How it was mapped (DICTIONARY/VECTOR/LLM/HUMAN/UNMAPPED)
- `similarity_score`: Confidence score (0-1)
- `low_confidence`: Flag for manual review

### 4. Invoice Module

#### **invoices**
- Uploaded invoice PDFs linked to quotes
- Multiple invoices can exist for one quote
- `file_path`: Storage location of PDF

#### **invoice_charges**
- Extracted charges from invoice PDF
- Same mapping structure as quote_charges
- Used for variance analysis

### 5. Anomaly Detection

#### **anomalies**
- Results of invoice vs quote comparison
- 6 types of anomalies:
  1. **AMOUNT_MISMATCH**: Invoice ≠ Quote amount
  2. **RATE_MISMATCH**: Rate changed
  3. **BASIS_MISMATCH**: Basis changed (Per KG → Per Shipment)
  4. **UNEXPECTED_CHARGE**: In invoice, not in quote
  5. **MISSING_CHARGE**: In quote, not in invoice
  6. **DUPLICATE_INVOICE**: Multiple invoices for same quote
- `variance`: Invoice - Quote (positive = overcharged)

### 6. Tracking

#### **tracking_events**
- Shipment tracking history
- Multiple events per quote
- Status examples: "Picked Up", "In Transit", "Delivered"

### 7. Audit

#### **audit_logs**
- Tracks important user actions
- Stores action type, entity, and details (JSONB)
- Useful for compliance and debugging

---

## Key Relationships

### One-to-Many (1:N)
- `countries` → `airports`
- `companies` → `profiles`
- `companies` → `charges`
- `charges` → `charge_aliases`
- `quotes` → `quote_charges`
- `quotes` → `invoices`
- `quotes` → `tracking_events`
- `invoices` → `invoice_charges`
- `invoices` → `anomalies`

### Many-to-One (N:1)
- `quotes` → `companies` (forwarder)
- `quotes` → `companies` (buyer)
- `quotes` → `airports` (origin)
- `quotes` → `airports` (destination)
- `quotes` → `currencies`
- `quote_charges` → `charges` (mapped)
- `invoice_charges` → `charges` (mapped)

---

## Indexes

### Performance Indexes
```sql
-- Foreign keys (automatic in most DBs)
companies.country_id
profiles.company_id
airports.country_id
charges.company_id
quotes.forwarder_id, buyer_id, origin_airport_id, destination_airport_id, currency_id
quote_charges.quote_id, mapped_charge_id
invoices.quote_id
invoice_charges.invoice_id, mapped_charge_id
anomalies.invoice_id
tracking_events.quote_id

-- Lookup fields
companies.type, is_active
profiles.email, role
airports.iata_code, is_active
quotes.quote_ref, tracking_number, status
invoices.invoice_number
charge_aliases.alias
```

---

## Constraints

### Unique Constraints
- `companies.name` (global)
- `companies.short_name` (global)
- `profiles.email` (global)
- `charges.(company_id, name)` (per company)
- `charges.(company_id, short_name)` (per company)
- `quotes.quote_ref` (global)
- `invoices.invoice_number` (global)

### Check Constraints
- `companies.type` IN ('client', 'forwarder')
- `profiles.role` IN ('super_admin', 'client', 'forwarder')
- `quotes.status` IN ('SUBMITTED', 'ACCEPTED', 'REJECTED')
- `quote_charges.basis` IN ('Per KG', 'Per Shipment', 'Per CBM')
- `anomalies.flag_type` IN (6 types)
- `quotes.forwarder_id` ≠ `quotes.buyer_id`
- Super admin has no company_id; others must have company_id

---

## Triggers

### 1. Auto-update `updated_at`
- Tables: `companies`, `profiles`, `charges`, `quotes`
- Automatically sets `updated_at = CURRENT_TIMESTAMP` on UPDATE

### 2. Auto-calculate `chargeable_weight`
- Table: `quotes`
- Sets `chargeable_weight = MAX(gross_weight, volumetric_weight)`

### 3. Cascade company deactivation
- When `companies.is_active` = FALSE
- Automatically sets `profiles.is_active` = FALSE for all company users

---

## Views

### 1. `v_quote_summary`
- Denormalized quote data with company names, airport codes
- Used for quote listing pages

### 2. `v_invoice_summary`
- Denormalized invoice data with quote and company info
- Used for invoice listing pages

### 3. `v_tracking_status`
- Latest tracking event per quote
- Shows current shipment status

---

## Data Isolation Rules

### Multi-Tenancy
- **Super Admin**: Can access all data
- **Client**: Can only see:
  - Quotes where `buyer_id` = their company
  - Invoices for their quotes
  - Anomalies for their invoices
  - Their own charges
- **Forwarder**: Can only see:
  - Quotes where `forwarder_id` = their company
  - Invoices for their quotes
  - Their own charges (if they have any)

### Implementation
- All queries must filter by `company_id` or related company fields
- Enforced at repository/service layer
- Never trust client-provided company_id

---

## Seed Data

### Included in Schema
- 10 countries (US, IN, GB, CN, DE, AE, SG, JP, AU, CA)
- 10 currencies (USD, INR, GBP, EUR, CNY, AED, SGD, JPY, AUD, CAD)
- 10 major airports (DEL, BOM, JFK, LAX, LHR, DXB, SIN, HKG, FRA, NRT)

### Test Data (Optional)
- 1 super admin user
- 3 companies (1 client, 2 forwarders)
- 2 company admin users
- 5 charges for client company
- 4 charge aliases

---

## Migration Strategy

### Using Alembic (Python) or similar tool

1. **Initial migration**: Create all tables
2. **Seed migration**: Insert master data
3. **Test data migration**: Insert test accounts (dev only)

### Example Alembic commands:
```bash
# Initialize
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Database Recommendations

### For Development
- **SQLite**: Simple, file-based, no setup
- **PostgreSQL (local)**: Full features, easy to migrate

### For Production
- **Neon PostgreSQL**: Serverless, auto-scaling, generous free tier
- **Supabase PostgreSQL**: Includes auth, storage, real-time
- **AWS RDS PostgreSQL**: Enterprise-grade, managed
- **Google Cloud SQL**: Managed PostgreSQL

### Recommended: **Neon PostgreSQL**
- ✅ Free tier: 3GB storage, 0.5GB RAM
- ✅ Serverless (auto-sleep when idle)
- ✅ Easy connection string
- ✅ Built-in backups
- ✅ Can upgrade to paid tier later

---

## Next Steps

1. **Choose database**: Neon PostgreSQL (recommended)
2. **Run schema**: Execute `database_schema.sql`
3. **Verify tables**: Check all 14 tables created
4. **Test seed data**: Verify countries, currencies, airports
5. **Create test accounts**: Use provided test data
6. **Build backend**: Start with auth endpoints

---

## Schema Statistics

- **Total Tables**: 14
  - Core: 13
  - Audit: 1
- **Total Views**: 3
- **Total Triggers**: 4
- **Total Indexes**: 30+
- **Seed Records**: 30 (countries, currencies, airports)
- **Test Records**: 10+ (companies, users, charges)

---

## Support for Features

✅ User & Company Management
✅ Role-Based Access Control
✅ Master Data Management
✅ Quote Submission & Review
✅ Charge Mapping (Dictionary/Vector/LLM/Human)
✅ Invoice Upload & Extraction
✅ Anomaly Detection (6 types)
✅ Variance Analysis
✅ Shipment Tracking
✅ Dashboard Analytics
✅ AI Copilot (query any table)
✅ Audit Logging
✅ Multi-Tenant Data Isolation
✅ Soft Deletes

---

**Schema Version**: 1.0
**Last Updated**: 2026-05-10
**Compatible With**: PostgreSQL 12+, MySQL 8+, SQLite 3.35+
