# Backend Rebuild - Requirements Document

## 1. Overview

### 1.1 Purpose
Complete rebuild of the LogiSight backend from scratch to work with a **pure frontend** that has zero external dependencies. The frontend is now a clean API contract/specification that only talks to your backend - no Supabase, no external services.

### 1.2 Approach
- **Frontend as Contract**: The frontend defines the complete API contract in `frontend/API_CONTRACT.md`
- **Pure Backend API**: Build backend that implements every endpoint the frontend expects
- **Feature-by-Feature**: Build and test each feature independently before moving to the next
- **Clean Slate**: Start fresh with proper architecture from day one
- **Database First**: Design proper database schema before implementing business logic
- **Agentic AI Friendly**: Each feature can be built independently by AI agents

### 1.3 Success Criteria
- All frontend features work correctly with the new backend
- Frontend has zero external dependencies (only backend API)
- Clean, maintainable code with proper separation of concerns
- Comprehensive test coverage for each feature
- Proper error handling and validation
- Production-ready authentication and authorization
- Well-documented APIs matching frontend contract

---

## 2. System Architecture Requirements

### 2.1 Technology Stack
- **Framework**: FastAPI (Python) - or any framework you prefer
- **Database**: PostgreSQL / SQLite / Any SQL database
- **Authentication**: JWT tokens (backend-managed)
- **ORM**: SQLAlchemy 2.0 (async) - or any ORM
- **API Documentation**: OpenAPI/Swagger

**Note**: You can use ANY tech stack - the frontend only cares about the HTTP API contract!

### 2.2 Architecture Principles
- **Clean Architecture**: Separate layers (API, Business Logic, Data Access)
- **Dependency Injection**: Proper DI for testability
- **Repository Pattern**: Abstract data access
- **Service Layer**: Business logic separate from API routes
- **DTO Pattern**: Clear request/response models
- **Error Handling**: Consistent error responses across all endpoints

### 2.3 Code Organization
```
backend/
├── app/
│   ├── api/              # API routes/controllers
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── quotes.py
│   │   │   ├── invoices.py
│   │   │   └── ...
│   ├── core/             # Core configuration
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas (DTOs)
│   ├── services/         # Business logic
│   ├── repositories/     # Data access layer
│   ├── utils/            # Utilities
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── alembic/              # Database migrations
```

---

## 3. Feature Requirements (Build Order)

### Phase 1: Foundation & Authentication

#### 3.1 Database Design & Connection
**User Story**: As a developer, I need a properly designed database schema that supports all features

**Requirements**:
- Design complete database schema based on frontend data models
- Implement connection pooling with proper configuration
- Set up Alembic for database migrations
- Create seed data scripts for development/testing
- Document all tables, relationships, and constraints

**Database Tables** (from frontend analysis):
- `companies` - Multi-tenant company records
- `profiles` - User profiles linked to Supabase auth
- `airports` - Master data for airports
- `currencies` - Master data for currencies
- `countries` - Master data for countries
- `charges` - Charge master (per company)
- `charge_aliases` - Charge name variations
- `quotes` - Quote headers
- `quote_charges` - Quote line items
- `invoices` - Invoice headers
- `invoice_charges` - Invoice line items
- `anomalies` - Detected discrepancies
- `tracking_events` - Shipment tracking

**Acceptance Criteria**:
- [ ] Complete ERD diagram created
- [ ] All tables created with proper constraints
- [ ] Foreign keys and indexes defined
- [ ] Migration scripts work cleanly
- [ ] Seed data populates test accounts
- [ ] Connection pool configured and tested

---

#### 3.2 Authentication & Authorization System
**User Story**: As a user, I need to securely log in and access features based on my role

**Roles** (from frontend):
1. **Super Admin** - Platform administrator, manages all companies
2. **Client Admin** - Company admin for client companies
3. **Client User** - Regular user for client companies
4. **Forwarder Admin** - Company admin for forwarder companies
5. **Forwarder User** - Regular user for forwarder companies

**Requirements**:

**3.2.1 JWT Token Validation**
- Integrate with Supabase Auth
- Support both ES256 and RS256 JWT algorithms
- Validate token signature using JWKS
- Extract user claims (role, company_id, is_admin)
- Cache JWKS with TTL for performance
- Handle token expiration gracefully

**3.2.2 Role-Based Access Control (RBAC)**
- Implement role checking middleware
- Create permission decorators for routes
- Define access rules per feature:
  - Super Admin: Full access to everything
  - Client Admin: Manage own company, users, charge master
  - Client User: View quotes, invoices, analyze
  - Forwarder Admin: Manage own company, users
  - Forwarder User: Submit quotes, upload invoices

**3.2.3 Multi-Tenant Data Isolation**
- Ensure users only access their company's data
- Implement company_id filtering at repository level
- Prevent cross-tenant data leakage
- Super admin can access all tenants

**API Endpoints**:
```
POST   /api/v1/auth/login          # Handled by Supabase (frontend direct)
POST   /api/v1/auth/logout         # Handled by Supabase (frontend direct)
GET    /api/v1/auth/me             # Get current user profile
POST   /api/v1/auth/refresh        # Refresh token (if needed)
```

**Acceptance Criteria**:
- [ ] JWT validation works for ES256 and RS256
- [ ] User claims extracted correctly from token
- [ ] Role-based access control enforced on all routes
- [ ] Multi-tenant isolation prevents data leakage
- [ ] Proper error messages for auth failures (401, 403)
- [ ] Test accounts work (all 5 roles)
- [ ] Token expiration handled gracefully

---

### Phase 2: Core Features

#### 3.3 Charge Master Management
**User Story**: As a client admin, I need to manage my company's charge master (standardized charge names and aliases)

**Requirements**:

**3.3.1 Charge CRUD Operations**
- Create new charges (name, short_name)
- Read charges (list, get by ID)
- Update charge details
- Soft delete charges (is_active flag)
- Charges are scoped per company

**3.3.2 Charge Alias Management**
- Add aliases to charges (variations of charge names)
- List aliases for a charge
- Delete aliases
- Aliases used for fuzzy matching during mapping

**API Endpoints**:
```
GET    /api/v1/charges              # List all charges for user's company
POST   /api/v1/charges              # Create new charge
GET    /api/v1/charges/{id}         # Get charge details
PATCH  /api/v1/charges/{id}         # Update charge
DELETE /api/v1/charges/{id}         # Soft delete charge

POST   /api/v1/charges/{id}/aliases # Add alias
DELETE /api/v1/charges/{id}/aliases/{alias_id} # Remove alias
```

**Frontend Expectations** (from `frontend/src/api/client.ts`):
```typescript
interface Charge {
  id: number;
  company_id: number;
  name: string;
  short_name: string;
  is_active: boolean;
  aliases: ChargeAlias[];
}

interface ChargeAlias {
  id: number;
  charge_id: number;
  alias: string;
}
```

**Acceptance Criteria**:
- [ ] Client admin can create/edit/delete charges
- [ ] Charges are isolated per company
- [ ] Aliases can be added/removed
- [ ] Duplicate charge names prevented within company
- [ ] Frontend charge master page works fully
- [ ] Proper validation and error messages

---

#### 3.4 Quote Management
**User Story**: As a forwarder, I need to submit quotes to clients, and as a client, I need to review and accept/reject quotes

**Requirements**:

**3.4.1 Quote Submission (Forwarder)**
- Submit quote with header info (origin, destination, weights, etc.)
- Include multiple charge line items
- Auto-generate quote reference number
- Set initial status to "SUBMITTED"
- Attempt automatic charge mapping using charge master

**3.4.2 Charge Mapping Pipeline**
- **Dictionary Match**: Exact match against charge names and aliases
- **Vector Similarity**: Fuzzy match using embeddings (if available)
- **LLM Fallback**: Use LLM for complex mappings (future)
- **Human Override**: Client can manually correct mappings
- Track mapping tier (DICTIONARY, VECTOR, LLM, HUMAN, UNMAPPED)
- Track confidence score and low_confidence flag

**3.4.3 Quote Review (Client)**
- List all quotes for client's company
- View quote details with all charges
- Accept or reject quote with optional note
- Only accepted quotes can have invoices uploaded

**API Endpoints**:
```
GET    /api/v1/quotes               # List quotes (filtered by role)
POST   /api/v1/quotes               # Submit new quote (forwarder only)
GET    /api/v1/quotes/{id}          # Get quote details
PATCH  /api/v1/quotes/{id}/status   # Accept/reject quote (client only)
PATCH  /api/v1/quotes/charges/{charge_id}/mapping # Correct charge mapping
```

**Frontend Expectations** (from `frontend/src/api/types.ts`):
```typescript
interface QuoteHeader {
  id: number;
  quote_ref: string;
  status: 'SUBMITTED' | 'ACCEPTED' | 'REJECTED';
  forwarder: CompanyRef;
  buyer: CompanyRef;
  origin_airport: AirportRef;
  destination_airport: AirportRef;
  tracking_number: string;
  gross_weight: number;
  volumetric_weight: number;
  chargeable_weight: number;
  currency: CurrencyRef;
  created_at: string;
}

interface QuoteDetail extends QuoteHeader {
  charges: ChargeLine[];
}

interface ChargeLine {
  id: number;
  raw_charge_name: string;
  mapped_charge_id: number | null;
  mapped_charge_name: string | null;
  similarity_score: number | null;
  mapping_tier: 'DICTIONARY' | 'VECTOR' | 'LLM' | 'HUMAN' | 'UNMAPPED';
  low_confidence: boolean;
  rate: number;
  basis: 'Per KG' | 'Per Shipment' | 'Per CBM';
  qty: number;
  amount: number;
}
```

**Acceptance Criteria**:
- [ ] Forwarder can submit quotes with multiple charges
- [ ] Quote reference auto-generated uniquely
- [ ] Charge mapping attempts dictionary match first
- [ ] Client can view all quotes for their company
- [ ] Client can accept/reject quotes
- [ ] Client can correct charge mappings
- [ ] Mapping corrections update aliases automatically
- [ ] Frontend quote pages work fully

---

#### 3.5 Invoice Management
**User Story**: As a forwarder, I need to upload invoices for accepted quotes, and as a client, I need to analyze invoices against quotes

**Requirements**:

**3.5.1 Invoice Upload (Forwarder)**
- Upload PDF invoice file for an accepted quote
- Store file in Supabase Storage
- Extract invoice data (OCR/manual entry)
- Create invoice record with charges
- Auto-generate invoice number
- Attempt charge mapping like quotes

**3.5.2 Invoice Data Extraction**
- Parse PDF to extract charges (Veryfi API or manual)
- Extract: charge names, rates, basis, quantities, amounts
- Create invoice_charges records
- Map charges to client's charge master

**3.5.3 Invoice Listing & Details**
- List invoices (filtered by role and company)
- View invoice details with all charges
- Show mapped vs unmapped charges
- Display confidence scores

**API Endpoints**:
```
GET    /api/v1/invoices             # List invoices
POST   /api/v1/invoices/upload      # Upload invoice PDF
GET    /api/v1/invoices/{id}        # Get invoice details
PATCH  /api/v1/invoices/charges/{charge_id}/mapping # Correct mapping
```

**Frontend Expectations**:
```typescript
interface InvoiceHeader {
  id: number;
  quote_id: number;
  invoice_number: string;
  invoice_date: string;
  file_path: string;
  uploaded_at: string;
  quote: QuoteHeader;
}

interface InvoiceDetail extends InvoiceHeader {
  charges: InvoiceChargeLine[];
}

interface InvoiceChargeLine extends ChargeLine {
  invoice_id: number;
}
```

**Acceptance Criteria**:
- [ ] Forwarder can upload invoice PDF
- [ ] File stored in Supabase Storage
- [ ] Invoice data extracted (manual entry acceptable for MVP)
- [ ] Charges mapped to charge master
- [ ] Client can view invoices for their quotes
- [ ] Client can correct charge mappings
- [ ] Frontend invoice pages work fully

---

#### 3.6 Anomaly Detection & Variance Analysis
**User Story**: As a client, I need to analyze invoices against accepted quotes to detect discrepancies

**Requirements**:

**3.6.1 Analysis Trigger**
- Client clicks "Analyze Invoice" button
- Backend compares invoice charges vs quote charges
- Detects multiple types of anomalies
- Stores anomalies in database
- Returns anomaly list to frontend

**3.6.2 Anomaly Types**
1. **AMOUNT_MISMATCH**: Invoice amount ≠ quote amount for same charge
2. **RATE_MISMATCH**: Rate changed between quote and invoice
3. **BASIS_MISMATCH**: Basis changed (e.g., Per KG → Per Shipment)
4. **UNEXPECTED_CHARGE**: Charge in invoice but not in quote
5. **MISSING_CHARGE**: Charge in quote but not in invoice
6. **DUPLICATE_INVOICE**: Multiple invoices for same quote

**3.6.3 Variance Calculation**
- Calculate total invoice amount
- Calculate total quote amount
- Calculate variance (invoice - quote)
- Show variance per charge
- Highlight charges with issues

**API Endpoints**:
```
POST   /api/v1/invoices/{id}/analyze    # Run analysis
GET    /api/v1/invoices/{id}/anomalies  # Get anomalies
```

**Frontend Expectations**:
```typescript
interface AnomalyRead {
  id: number;
  invoice_id: number;
  invoice_charge_id: number | null;
  flag_type: 'AMOUNT_MISMATCH' | 'RATE_MISMATCH' | 'BASIS_MISMATCH' | 
             'UNEXPECTED_CHARGE' | 'MISSING_CHARGE' | 'DUPLICATE_INVOICE';
  description: string;
  variance: number | null;
}
```

**Analysis Logic**:
```
For each invoice charge:
  - Find matching quote charge (by mapped_charge_id)
  - If no match → UNEXPECTED_CHARGE
  - If match:
    - Compare amounts → AMOUNT_MISMATCH if different
    - Compare rates → RATE_MISMATCH if different
    - Compare basis → BASIS_MISMATCH if different

For each quote charge:
  - Check if exists in invoice
  - If missing → MISSING_CHARGE

Check for duplicate invoices:
  - Query invoices with same quote_id
  - If multiple → DUPLICATE_INVOICE
```

**Acceptance Criteria**:
- [ ] Analyze button triggers backend analysis
- [ ] All 6 anomaly types detected correctly
- [ ] Variance calculated accurately
- [ ] Anomalies stored in database
- [ ] Frontend displays anomalies with descriptions
- [ ] Variance shown in UI (invoice total vs quote total)
- [ ] Analysis can be re-run (clears old anomalies)

---

### Phase 3: Advanced Features

#### 3.7 Tracking & Shipment Status
**User Story**: As a user, I need to track shipment status and view tracking events

**Requirements**:
- List all shipments with current status
- View tracking events for a shipment
- Update tracking status (forwarder)
- Show timeline of events

**API Endpoints**:
```
GET    /api/v1/tracking                    # List all shipments
GET    /api/v1/tracking/{quote_id}/events  # Get tracking events
POST   /api/v1/tracking/{quote_id}/events  # Add tracking event
```

**Acceptance Criteria**:
- [ ] Tracking page shows all shipments
- [ ] Events displayed in timeline
- [ ] Status updates work
- [ ] Frontend tracking page works

---

#### 3.8 AI Copilot (LLM Query System)
**User Story**: As a user, I need to ask natural language questions about my data

**Requirements**:

**3.8.1 Query Processing**
- Accept natural language question
- Convert to SQL query using LLM
- Execute query safely (read-only)
- Return results in natural language

**3.8.2 Context & Scope**
- User can only query their company's data
- Provide schema context to LLM
- Include sample queries for better results
- Handle errors gracefully

**3.8.3 Query Types**
- "How many quotes are pending?"
- "What's the total value of accepted quotes this month?"
- "Show me invoices with anomalies"
- "Which charges have the most discrepancies?"

**API Endpoints**:
```
POST   /api/v1/copilot/query    # Ask question, get answer
```

**Frontend Expectations**:
```typescript
interface CopilotQueryRequest {
  question: string;
}

interface CopilotQueryResponse {
  answer: string;
}
```

**Acceptance Criteria**:
- [ ] LLM converts questions to SQL
- [ ] Queries execute safely (read-only, scoped to company)
- [ ] Results returned in natural language
- [ ] Frontend copilot page works
- [ ] Error handling for invalid queries

---

#### 3.9 Dashboard & Analytics
**User Story**: As a user, I need to see key metrics and statistics

**Requirements**:
- Show open quotes count
- Show invoices this month
- Show total accepted quotes
- Show pending anomalies count
- Role-specific metrics

**API Endpoints**:
```
GET    /api/v1/dashboard/stats    # Get dashboard statistics
```

**Acceptance Criteria**:
- [ ] Dashboard shows correct metrics
- [ ] Metrics filtered by company
- [ ] Frontend dashboard works

---

#### 3.10 Company & User Management (Super Admin)
**User Story**: As a super admin, I need to manage companies and users

**Requirements**:
- Create new companies (client/forwarder)
- Activate/deactivate companies
- Create admin users for companies
- View all companies and users

**API Endpoints**:
```
GET    /api/v1/companies           # List all companies
POST   /api/v1/companies           # Create company
PATCH  /api/v1/companies/{id}      # Update company
POST   /api/v1/companies/{id}/users # Create user for company
```

**Acceptance Criteria**:
- [ ] Super admin can create companies
- [ ] Super admin can create admin users
- [ ] Company activation/deactivation works
- [ ] Frontend super admin page works

---

## 4. Non-Functional Requirements

### 4.1 Performance
- API response time < 200ms for simple queries
- API response time < 2s for complex analysis
- Support 100+ concurrent users
- Database queries optimized with indexes

### 4.2 Security
- All endpoints require authentication (except health check)
- JWT tokens validated on every request
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)
- CORS configured properly
- Secrets stored in environment variables

### 4.3 Error Handling
- Consistent error response format
- Proper HTTP status codes
- Detailed error messages for debugging
- User-friendly error messages for frontend
- Logging of all errors

### 4.4 Testing
- Unit tests for all services
- Integration tests for all API endpoints
- E2E tests for critical flows
- Test coverage > 80%
- Test data fixtures for all scenarios

### 4.5 Documentation
- OpenAPI/Swagger docs auto-generated
- README with setup instructions
- Architecture documentation
- API endpoint documentation
- Database schema documentation

### 4.6 Deployment
- Docker containerization
- Environment-based configuration
- Database migration scripts
- Health check endpoint
- Logging and monitoring

---

## 5. Data Models & Contracts

### 5.1 Frontend Data Models (Reference)
All backend responses must match these TypeScript interfaces from the frontend:

**Location**: `frontend/src/api/types.ts`

Key interfaces:
- `Company`, `CompanyRef`
- `UserProfile`, `UserRole`
- `Charge`, `ChargeAlias`
- `QuoteHeader`, `QuoteDetail`, `QuoteSubmitPayload`
- `InvoiceHeader`, `InvoiceDetail`
- `ChargeLine`, `InvoiceChargeLine`
- `AnomalyRead`, `AnomalyFlagType`
- `TrackingShipment`, `TrackingEvent`
- `Airport`, `Currency`, `Country`

### 5.2 API Response Format
```json
{
  "data": { ... },           // Success response
  "error": {                 // Error response
    "code": "ERROR_CODE",
    "message": "User-friendly message",
    "details": { ... }       // Optional debug info
  }
}
```

---

## 6. Testing Strategy

### 6.1 Test Pyramid
- **Unit Tests** (70%): Test services, repositories, utilities
- **Integration Tests** (20%): Test API endpoints with test database
- **E2E Tests** (10%): Test complete flows with frontend

### 6.2 Test Data
- Use test database (separate from dev/prod)
- Seed test companies and users
- Create test quotes and invoices
- Reset database between test runs

### 6.3 Test Coverage Goals
- Services: 90%+
- Repositories: 80%+
- API Routes: 80%+
- Overall: 80%+

---

## 7. Migration Strategy

### 7.1 Approach
1. **Keep frontend running** with old backend initially
2. **Build new backend** in parallel (different port)
3. **Test each feature** against frontend as it's built
4. **Switch frontend** to new backend feature by feature
5. **Deprecate old backend** once all features migrated

### 7.2 Rollback Plan
- Keep old backend code in separate branch
- Can switch frontend back to old backend if needed
- Database migrations are reversible

---

## 8. Success Metrics

### 8.1 Functional Metrics
- [ ] All frontend pages work without errors
- [ ] All user roles can perform their tasks
- [ ] All test accounts work correctly
- [ ] No data leakage between companies
- [ ] All anomaly types detected correctly

### 8.2 Quality Metrics
- [ ] Test coverage > 80%
- [ ] No critical security vulnerabilities
- [ ] API response times meet targets
- [ ] Zero SQL injection vulnerabilities
- [ ] All endpoints documented

### 8.3 Developer Experience
- [ ] Clear code structure and organization
- [ ] Easy to add new features
- [ ] Easy to debug issues
- [ ] Good error messages
- [ ] Comprehensive documentation

---

## 9. Out of Scope (Future Enhancements)

These features are not included in the initial rebuild but can be added later:

- Real-time notifications
- Email notifications
- Advanced analytics and reporting
- Bulk operations (bulk upload, bulk approve)
- API rate limiting
- Caching layer (Redis)
- Microservices architecture
- Event-driven architecture
- Advanced ML for charge mapping
- Mobile app support
- Multi-language support
- Audit logging
- Data export (CSV, Excel)
- Advanced search and filtering

---

## 10. Timeline Estimate

**Phase 1: Foundation** (1-2 weeks)
- Database design: 2-3 days
- Authentication: 3-4 days
- Testing setup: 1-2 days

**Phase 2: Core Features** (3-4 weeks)
- Charge Master: 3-4 days
- Quote Management: 5-7 days
- Invoice Management: 5-7 days
- Anomaly Detection: 3-4 days

**Phase 3: Advanced Features** (2-3 weeks)
- Tracking: 2-3 days
- AI Copilot: 5-7 days
- Dashboard: 2-3 days
- Admin Features: 3-4 days

**Total: 6-9 weeks** for complete rebuild

---

## 11. Next Steps

1. **Review this requirements document** - Confirm all features and priorities
2. **Create design document** - Define architecture, API specs, database schema
3. **Set up development environment** - New backend project structure
4. **Start with Phase 1** - Database and authentication
5. **Build feature by feature** - Test each against frontend before moving on

---

## Appendix A: Frontend API Client Reference

**File**: `frontend/src/api/client.ts`

This file contains all API calls the frontend makes. Each function defines:
- Endpoint URL
- Request payload structure
- Response data structure
- Error handling expectations

Use this as the definitive contract for what the backend must provide.

---

## Appendix B: Current Backend Issues

Issues with current backend that the rebuild will fix:

1. **Patchwork code** - No clear architecture
2. **Mixed concerns** - Business logic in routes
3. **Inconsistent error handling** - Different error formats
4. **No proper testing** - Hard to verify correctness
5. **JWT algorithm mismatch** - Had to patch ES256 support
6. **Duplicate logic** - Frontend and backend both do analysis
7. **No validation** - Missing input validation
8. **Poor separation** - Hard to maintain and extend
9. **No documentation** - Hard to understand what endpoints do
10. **Security gaps** - Potential data leakage, no proper RBAC

The rebuild addresses all of these systematically.
