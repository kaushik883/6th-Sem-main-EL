# Feature Implementation Checklist

Use this checklist when Antigravity builds each feature to ensure nothing is missed.

---

## ✅ General Requirements (Every Feature)

### Authentication & Authorization
- [ ] Endpoint requires JWT token (except /auth/login)
- [ ] `get_current_user` dependency used
- [ ] Role-based access control enforced
- [ ] Returns 401 if not authenticated
- [ ] Returns 403 if not authorized

### Data Isolation
- [ ] Queries filter by company_id (where applicable)
- [ ] Super admin can access all data
- [ ] Users can only access their company's data
- [ ] No cross-tenant data leakage

### Validation
- [ ] All required fields validated
- [ ] Field types validated (string, int, decimal, etc.)
- [ ] Field lengths validated (min/max)
- [ ] Foreign keys validated (references exist)
- [ ] Business rules validated (e.g., buyer ≠ forwarder)

### Error Handling
- [ ] Proper HTTP status codes (400, 401, 403, 404, 500)
- [ ] Consistent error response format
- [ ] User-friendly error messages
- [ ] Validation errors include field details

### Database
- [ ] Uses SQLAlchemy models
- [ ] Proper transactions (commit/rollback)
- [ ] Handles database errors gracefully
- [ ] Uses indexes for performance

### Response Format
- [ ] Matches TypeScript interface from `frontend/src/api/types.ts`
- [ ] Includes all required fields
- [ ] Proper data types (numbers as numbers, not strings)
- [ ] Nested objects populated correctly

---

## 🔐 Feature 1: Authentication

### POST /auth/login
- [ ] Accepts email and password
- [ ] Validates email format
- [ ] Queries profiles table
- [ ] Checks user is_active = TRUE
- [ ] Checks company is_active = TRUE (if not super admin)
- [ ] Verifies password hash (bcrypt)
- [ ] Creates JWT token with user_id, role, company_id
- [ ] Returns token and user object
- [ ] Returns 401 if invalid credentials
- [ ] Returns 401 if user/company deactivated

### GET /auth/me
- [ ] Requires authentication
- [ ] Returns current user profile
- [ ] Includes company info (if applicable)
- [ ] Returns 401 if token invalid

---

## 🏢 Feature 2: Company Management (Super Admin)

### GET /companies
- [ ] Only super admin can access
- [ ] Returns all companies (active and inactive)
- [ ] Includes company details
- [ ] Returns 403 if not super admin

### POST /companies
- [ ] Only super admin can access
- [ ] Validates company name unique
- [ ] Validates short name unique
- [ ] Validates email unique
- [ ] Hashes password
- [ ] Creates company record
- [ ] Creates admin user record
- [ ] Links user to company
- [ ] Sets is_admin = TRUE
- [ ] Returns company with admin user
- [ ] Returns 400 if validation fails

### PATCH /companies/{id}/status
- [ ] Only super admin can access
- [ ] Validates company exists
- [ ] Updates is_active flag
- [ ] Cascades to users (deactivate all users if company deactivated)
- [ ] Returns updated company
- [ ] Returns 404 if company not found

---

## 📊 Feature 3: Master Data

### GET /masters/airports
- [ ] Returns all active airports
- [ ] Includes country info
- [ ] Filters is_active = TRUE
- [ ] No authentication required (or authenticated users only)

### GET /masters/currencies
- [ ] Returns all active currencies
- [ ] Filters is_active = TRUE
- [ ] No authentication required (or authenticated users only)

---

## 💰 Feature 4: Charge Master (Client)

### GET /charges
- [ ] Only clients can access
- [ ] Returns charges for user's company
- [ ] Includes aliases
- [ ] Filters by company_id
- [ ] Returns 403 if not client

### POST /charges
- [ ] Only client admins can access
- [ ] Validates name unique within company
- [ ] Validates short_name unique within company
- [ ] Creates charge record
- [ ] Sets company_id = user.company_id
- [ ] Returns charge
- [ ] Returns 400 if duplicate name
- [ ] Returns 403 if not admin

### PATCH /charges/{id}
- [ ] Only client admins can access
- [ ] Validates charge belongs to user's company
- [ ] Updates name/short_name/is_active
- [ ] Validates uniqueness if name changed
- [ ] Returns updated charge
- [ ] Returns 403 if not owner
- [ ] Returns 404 if not found

### POST /charges/{chargeId}/aliases
- [ ] Only client admins can access
- [ ] Validates charge belongs to user's company
- [ ] Validates alias doesn't already exist
- [ ] Creates alias record
- [ ] Returns alias
- [ ] Returns 400 if duplicate alias

### DELETE /charges/aliases/{aliasId}
- [ ] Only client admins can access
- [ ] Validates alias belongs to user's company (via charge)
- [ ] Deletes alias record
- [ ] Returns 204 No Content
- [ ] Returns 403 if not owner

---

## 📋 Feature 5: Quote Management

### GET /quotes
- [ ] Filters by user role:
  - Forwarder: forwarder_id = user.company_id
  - Client: buyer_id = user.company_id
  - Super admin: all quotes
- [ ] Returns quote headers (not charges)
- [ ] Includes company names, airport codes
- [ ] Sorted by created_at DESC

### POST /quotes
- [ ] Only forwarders can access
- [ ] Validates buyer_id is client company
- [ ] Validates buyer_id ≠ forwarder_id
- [ ] Generates quote_ref: "{ShortName}-{YYYY}-{AutoIncrement}"
- [ ] Calculates chargeable_weight = MAX(gross, volumetric)
- [ ] Sets status = 'SUBMITTED'
- [ ] Sets forwarder_id = user.company_id
- [ ] Creates quote record
- [ ] For each charge:
  - Attempts charge mapping to buyer's charge master
  - Sets mapping_tier (DICTIONARY/UNMAPPED)
  - Calculates qty based on basis
  - Calculates amount = rate × qty
  - Creates quote_charge record
- [ ] Returns complete quote with charges
- [ ] Returns 403 if not forwarder
- [ ] Returns 400 if validation fails

### GET /quotes/{id}
- [ ] Validates user has access (forwarder or buyer)
- [ ] Returns quote with all charges
- [ ] Includes mapping info
- [ ] Returns 403 if not owner
- [ ] Returns 404 if not found

### PATCH /quotes/{id}/status
- [ ] Only clients can access
- [ ] Validates quote buyer_id = user.company_id
- [ ] Validates current status = 'SUBMITTED'
- [ ] Updates status to ACCEPTED/REJECTED
- [ ] Sets rejection_note if rejecting
- [ ] Returns updated quote
- [ ] Returns 403 if not buyer
- [ ] Returns 400 if already processed
- [ ] Returns 400 if rejecting without note

### PATCH /quotes/charges/{chargeId}/mapping
- [ ] Only clients can access
- [ ] Validates charge belongs to user's quote
- [ ] Validates mapped_charge_id belongs to user's company
- [ ] Updates mapped_charge_id
- [ ] Sets mapping_tier = 'HUMAN'
- [ ] Sets low_confidence = FALSE
- [ ] Adds raw_charge_name as alias (if not exists)
- [ ] Returns 204 No Content
- [ ] Returns 403 if not owner

---

## 📄 Feature 6: Invoice Management

### GET /invoices
- [ ] Filters by user role:
  - Forwarder: quote.forwarder_id = user.company_id
  - Client: quote.buyer_id = user.company_id
  - Super admin: all invoices
- [ ] Supports quote_id filter (optional)
- [ ] Returns invoice headers (not charges)
- [ ] Includes quote info
- [ ] Sorted by uploaded_at DESC

### POST /invoices/upload
- [ ] Only forwarders can access
- [ ] Validates quote exists
- [ ] Validates quote.forwarder_id = user.company_id
- [ ] Validates quote.status = 'ACCEPTED'
- [ ] Validates file is PDF
- [ ] Validates file size < 10MB
- [ ] Stores file (filesystem or cloud)
- [ ] Generates invoice_number
- [ ] Extracts charges (or accepts manual entry)
- [ ] For each charge:
  - Attempts charge mapping to buyer's charge master
  - Creates invoice_charge record
- [ ] Creates invoice record
- [ ] Returns complete invoice with charges
- [ ] Returns 403 if not forwarder
- [ ] Returns 400 if quote not accepted
- [ ] Returns 400 if invalid file

### GET /invoices/{id}
- [ ] Validates user has access (forwarder or buyer)
- [ ] Returns invoice with all charges
- [ ] Includes mapping info
- [ ] Returns 403 if not owner
- [ ] Returns 404 if not found

### POST /invoices/{id}/analyze
- [ ] Only clients can access
- [ ] Validates invoice.quote.buyer_id = user.company_id
- [ ] Deletes old anomalies for this invoice
- [ ] Compares invoice charges vs quote charges:
  - AMOUNT_MISMATCH: amounts differ
  - RATE_MISMATCH: rates differ
  - BASIS_MISMATCH: basis differs
  - UNEXPECTED_CHARGE: in invoice, not in quote
  - MISSING_CHARGE: in quote, not in invoice
  - DUPLICATE_INVOICE: multiple invoices for quote
- [ ] Creates anomaly records
- [ ] Returns anomalies list
- [ ] Returns 403 if not buyer

### GET /invoices/{id}/anomalies
- [ ] Only clients can access
- [ ] Validates invoice.quote.buyer_id = user.company_id
- [ ] Returns anomalies for invoice
- [ ] Returns 403 if not buyer

### PATCH /invoices/charges/{chargeId}/mapping
- [ ] Only clients can access
- [ ] Validates charge belongs to user's invoice
- [ ] Updates mapped_charge_id
- [ ] Sets mapping_tier = 'HUMAN'
- [ ] Adds raw_charge_name as alias
- [ ] Returns 204 No Content
- [ ] Returns 403 if not owner

---

## 📍 Feature 7: Tracking

### GET /tracking
- [ ] Filters by user role:
  - Forwarder: quote.forwarder_id = user.company_id
  - Client: quote.buyer_id = user.company_id
  - Super admin: all shipments
- [ ] Returns shipments with latest tracking event
- [ ] Includes quote info, current status
- [ ] Sorted by last_event_time DESC

### GET /tracking/{quoteId}/events
- [ ] Validates user has access to quote
- [ ] Returns all tracking events for quote
- [ ] Sorted by event_time ASC
- [ ] Returns 403 if not owner
- [ ] Returns 404 if quote not found

---

## 🤖 Feature 8: AI Copilot (Client)

### POST /copilot/query
- [ ] Only clients can access
- [ ] Accepts natural language question
- [ ] Converts question to SQL using LLM
- [ ] Validates SQL is read-only (SELECT only)
- [ ] Scopes query to user's company
- [ ] Executes query safely
- [ ] Formats results as natural language
- [ ] Returns answer
- [ ] Returns 403 if not client
- [ ] Returns 400 if invalid query
- [ ] Handles SQL errors gracefully

---

## 📊 Feature 9: Dashboard

### GET /dashboard/stats
- [ ] Filters by user role and company
- [ ] Returns:
  - open_quotes: count of SUBMITTED quotes
  - anomalies_pending: count of unresolved anomalies
  - invoices_this_month: count of invoices this month
  - total_accepted: count of ACCEPTED quotes
- [ ] All counts scoped to user's company
- [ ] Returns 0 for counts if no data

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] Service layer functions tested
- [ ] Business logic tested
- [ ] Edge cases tested
- [ ] Error handling tested

### Integration Tests
- [ ] API endpoints tested
- [ ] Database queries tested
- [ ] Authentication tested
- [ ] Authorization tested

### Frontend Integration
- [ ] Login page works
- [ ] Feature page loads without errors
- [ ] Data displays correctly
- [ ] Forms submit successfully
- [ ] Error messages show correctly
- [ ] No console errors
- [ ] Network tab shows correct requests/responses

---

## 📝 Code Quality Checklist

### Code Organization
- [ ] Models in `app/models/`
- [ ] Schemas in `app/schemas/`
- [ ] Services in `app/services/`
- [ ] Repositories in `app/repositories/`
- [ ] Routes in `app/api/v1/`

### Code Style
- [ ] Type hints used
- [ ] Docstrings for functions
- [ ] Consistent naming conventions
- [ ] No hardcoded values (use config)
- [ ] No commented-out code

### Performance
- [ ] Database queries optimized
- [ ] Indexes used for lookups
- [ ] N+1 queries avoided
- [ ] Pagination for large lists (if needed)

---

## 🚀 Deployment Checklist

### Environment Variables
- [ ] DATABASE_URL configured
- [ ] JWT_SECRET configured
- [ ] CORS origins configured
- [ ] File storage path configured

### Database
- [ ] Migrations run
- [ ] Seed data loaded
- [ ] Indexes created
- [ ] Constraints enforced

### Security
- [ ] Passwords hashed (bcrypt)
- [ ] JWT tokens signed
- [ ] HTTPS enforced (production)
- [ ] CORS configured correctly
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevented (input sanitization)

---

**Use this checklist for EVERY feature Antigravity builds!** ✅
