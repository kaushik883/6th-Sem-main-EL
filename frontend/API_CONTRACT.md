# Backend API Contract

This document defines the complete API contract that the backend must implement for the frontend to work.

## Base URL
```
http://localhost:8001
```

## Authentication
All endpoints (except `/auth/login`) require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## 1. Authentication Endpoints

### POST `/auth/login`
Login with email and password.

**Request:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "string (JWT token)",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "role": "super_admin" | "client" | "forwarder",
    "company_id": number | null,
    "company_type": "client" | "forwarder" | undefined,
    "company_name": "string" | undefined,
    "is_admin": boolean
  }
}
```

### POST `/auth/logout`
Logout current user (optional - frontend clears token).

**Response:** `204 No Content`

### GET `/auth/me`
Get current user profile.

**Response:**
```json
{
  "id": "string",
  "email": "string",
  "name": "string",
  "role": "super_admin" | "client" | "forwarder",
  "company_id": number | null,
  "company_type": "client" | "forwarder" | undefined,
  "company_name": "string" | undefined,
  "is_admin": boolean
}
```

---

## 2. Company Endpoints

### GET `/companies`
List all companies (super_admin only).

**Response:**
```json
[
  {
    "id": number,
    "name": "string",
    "short_name": "string",
    "type": "client" | "forwarder",
    "address": "string" | null,
    "city": "string" | null,
    "country": "string" | null,
    "is_active": boolean,
    "created_at": "string (ISO date)"
  }
]
```

### POST `/companies`
Create a new company with admin user (super_admin only).

**Request:**
```json
{
  "name": "string",
  "short_name": "string",
  "type": "client" | "forwarder",
  "address": "string" | null,
  "city": "string" | null,
  "country": "string" | null,
  "admin_email": "string",
  "admin_name": "string",
  "admin_password": "string"
}
```

**Response:** Company object (same as GET)

### PATCH `/companies/{id}/status`
Activate/deactivate a company (super_admin only).

**Request:**
```json
{
  "is_active": boolean
}
```

**Response:** Company object

---

## 3. Master Data Endpoints

### GET `/masters/airports`
List all active airports.

**Response:**
```json
[
  {
    "id": number,
    "name": "string",
    "iata_code": "string",
    "country_id": number | null,
    "is_active": boolean
  }
]
```

### GET `/masters/currencies`
List all active currencies.

**Response:**
```json
[
  {
    "id": number,
    "name": "string",
    "short_name": "string",
    "is_active": boolean
  }
]
```

---

## 4. Charge Master Endpoints

### GET `/charges`
List all charges for the current user's company.

**Response:**
```json
[
  {
    "id": number,
    "company_id": number,
    "name": "string",
    "short_name": "string",
    "is_active": boolean,
    "aliases": [
      {
        "id": number,
        "charge_id": number,
        "alias": "string"
      }
    ]
  }
]
```

### POST `/charges`
Create a new charge (client_admin only).

**Request:**
```json
{
  "name": "string",
  "short_name": "string"
}
```

**Response:** Charge object (same as GET)

### PATCH `/charges/{id}`
Update a charge (client_admin only).

**Request:**
```json
{
  "name": "string" | undefined,
  "short_name": "string" | undefined,
  "is_active": boolean | undefined
}
```

**Response:** Charge object

### POST `/charges/{chargeId}/aliases`
Add an alias to a charge.

**Request:**
```json
{
  "alias": "string"
}
```

**Response:**
```json
{
  "id": number,
  "charge_id": number,
  "alias": "string"
}
```

### DELETE `/charges/aliases/{aliasId}`
Delete an alias.

**Response:** `204 No Content`

---

## 5. Quote Endpoints

### GET `/quotes`
List all quotes (filtered by user's company and role).

**Response:**
```json
[
  {
    "id": number,
    "quote_ref": "string",
    "status": "SUBMITTED" | "ACCEPTED" | "REJECTED",
    "rejection_note": "string" | null,
    "created_at": "string (ISO date)",
    "forwarder": {
      "id": number,
      "name": "string"
    },
    "buyer": {
      "id": number,
      "name": "string"
    },
    "origin_airport": {
      "iata_code": "string",
      "name": "string"
    },
    "destination_airport": {
      "iata_code": "string",
      "name": "string"
    },
    "tracking_number": "string",
    "gross_weight": number,
    "volumetric_weight": number,
    "chargeable_weight": number,
    "currency": {
      "short_name": "string"
    }
  }
]
```

### GET `/quotes/{id}`
Get quote details with charges.

**Response:** Quote object (same as list) plus:
```json
{
  ...quote_fields,
  "charges": [
    {
      "id": number,
      "raw_charge_name": "string",
      "mapped_charge_id": number | null,
      "mapped_charge_name": "string" | null,
      "similarity_score": number | null,
      "mapping_tier": "DICTIONARY" | "VECTOR" | "LLM" | "HUMAN" | "UNMAPPED",
      "low_confidence": boolean,
      "rate": number,
      "basis": "Per KG" | "Per Shipment" | "Per CBM",
      "qty": number,
      "amount": number
    }
  ]
}
```

### POST `/quotes`
Submit a new quote (forwarder only).

**Request:**
```json
{
  "buyer_id": number,
  "origin_airport_id": number,
  "destination_airport_id": number,
  "tracking_number": "string",
  "gross_weight": number,
  "volumetric_weight": number,
  "chargeable_weight": number,
  "currency_id": number,
  "charges": [
    {
      "raw_charge_name": "string",
      "rate": number,
      "basis": "Per KG" | "Per Shipment" | "Per CBM",
      "qty": number,
      "amount": number
    }
  ]
}
```

**Response:** Quote detail object (with charges)

**Backend Logic:**
- Auto-generate `quote_ref` (e.g., "QR-{timestamp}")
- Set `forwarder_id` from authenticated user's company
- Set initial `status` to "SUBMITTED"
- Attempt charge mapping (dictionary match against buyer's charge master)
- Set `mapping_tier` and `low_confidence` based on match quality

### PATCH `/quotes/{id}/status`
Accept or reject a quote (client only).

**Request:**
```json
{
  "status": "ACCEPTED" | "REJECTED",
  "rejection_note": "string" | undefined
}
```

**Response:** Quote detail object

### PATCH `/quotes/charges/{chargeId}/mapping`
Correct a charge mapping (client only).

**Request:**
```json
{
  "mapped_charge_id": number
}
```

**Response:** `204 No Content`

**Backend Logic:**
- Update `mapped_charge_id` and `mapped_charge_name`
- Set `mapping_tier` to "HUMAN"
- Set `low_confidence` to false
- Add `raw_charge_name` as alias to the charge master

---

## 6. Invoice Endpoints

### GET `/invoices`
List all invoices (filtered by user's company and role).

**Query Parameters:**
- `quote_id` (optional): Filter by quote ID

**Response:**
```json
[
  {
    "id": number,
    "quote_id": number,
    "invoice_number": "string",
    "invoice_date": "string (YYYY-MM-DD)",
    "file_path": "string",
    "uploaded_at": "string (ISO date)",
    "quote": {
      ...quote_header_fields
    }
  }
]
```

### GET `/invoices/{id}`
Get invoice details with charges.

**Response:** Invoice object (same as list) plus:
```json
{
  ...invoice_fields,
  "charges": [
    {
      "id": number,
      "invoice_id": number,
      "raw_charge_name": "string",
      "mapped_charge_id": number | null,
      "mapped_charge_name": "string" | null,
      "similarity_score": number | null,
      "mapping_tier": "DICTIONARY" | "VECTOR" | "LLM" | "HUMAN" | "UNMAPPED",
      "low_confidence": boolean,
      "rate": number,
      "basis": "Per KG" | "Per Shipment" | "Per CBM",
      "qty": number,
      "amount": number
    }
  ]
}
```

### POST `/invoices/upload`
Upload an invoice PDF (forwarder only).

**Request:** `multipart/form-data`
- `quote_id`: number
- `file`: File (PDF)

**Response:** Invoice detail object

**Backend Logic:**
- Validate quote exists and is ACCEPTED
- Store file (local filesystem or cloud storage)
- Auto-generate `invoice_number` (e.g., "INV-{timestamp}")
- Extract invoice data (OCR or manual entry)
- Create invoice_charges records
- Attempt charge mapping against buyer's charge master

### POST `/invoices/{id}/analyze`
Analyze invoice against quote (client only).

**Response:**
```json
[
  {
    "id": number,
    "invoice_id": number,
    "invoice_charge_id": number | null,
    "flag_type": "AMOUNT_MISMATCH" | "RATE_MISMATCH" | "BASIS_MISMATCH" | "UNEXPECTED_CHARGE" | "MISSING_CHARGE" | "DUPLICATE_INVOICE",
    "description": "string",
    "variance": number | null
  }
]
```

**Backend Logic:**
- Compare invoice charges vs quote charges (by mapped_charge_id)
- Detect 6 types of anomalies:
  1. **AMOUNT_MISMATCH**: Invoice amount ≠ quote amount
  2. **RATE_MISMATCH**: Rate changed
  3. **BASIS_MISMATCH**: Basis changed (e.g., Per KG → Per Shipment)
  4. **UNEXPECTED_CHARGE**: Charge in invoice but not in quote
  5. **MISSING_CHARGE**: Charge in quote but not in invoice
  6. **DUPLICATE_INVOICE**: Multiple invoices for same quote
- Delete old anomalies for this invoice
- Insert new anomalies
- Return anomaly list

### GET `/invoices/{id}/anomalies`
Get anomalies for an invoice.

**Response:** Array of anomaly objects (same as analyze)

### PATCH `/invoices/charges/{chargeId}/mapping`
Correct an invoice charge mapping (client only).

**Request:**
```json
{
  "mapped_charge_id": number
}
```

**Response:** `204 No Content`

**Backend Logic:** Same as quote charge mapping correction

---

## 7. Tracking Endpoints

### GET `/tracking`
List all shipments with tracking status.

**Response:**
```json
[
  {
    "quote_id": number,
    "quote_ref": "string",
    "tracking_number": "string",
    "origin": "string (IATA code)",
    "destination": "string (IATA code)",
    "current_status": "string",
    "last_event_time": "string (ISO date)",
    "forwarder_name": "string",
    "buyer_name": "string"
  }
]
```

**Backend Logic:**
- Join quotes with tracking_events
- Get latest event for each quote
- Return aggregated tracking info

### GET `/tracking/{quoteId}/events`
Get tracking events for a shipment.

**Response:**
```json
[
  {
    "id": number,
    "quote_id": number,
    "event_time": "string (ISO date)",
    "location": "string",
    "status": "string",
    "description": "string"
  }
]
```

---

## 8. Copilot Endpoint

### POST `/copilot/query`
Ask a natural language question about data (client only).

**Request:**
```json
{
  "question": "string"
}
```

**Response:**
```json
{
  "answer": "string"
}
```

**Backend Logic:**
- Use LLM to convert question to SQL
- Execute query (read-only, scoped to user's company)
- Format results as natural language answer
- Handle errors gracefully

---

## 9. Dashboard Endpoint

### GET `/dashboard/stats`
Get dashboard statistics.

**Response:**
```json
{
  "open_quotes": number,
  "anomalies_pending": number,
  "invoices_this_month": number,
  "total_accepted": number
}
```

**Backend Logic:**
- Filter by user's company
- Count quotes with status="SUBMITTED"
- Count invoices uploaded this month
- Count quotes with status="ACCEPTED"
- Count anomalies not resolved

---

## Error Responses

All endpoints should return consistent error responses:

**400 Bad Request:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-friendly error message",
    "details": {
      "field": "error details"
    }
  }
}
```

**401 Unauthorized:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

**403 Forbidden:**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions"
  }
}
```

**404 Not Found:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found"
  }
}
```

**500 Internal Server Error:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

---

## Role-Based Access Control

### Roles:
1. **super_admin** - Platform administrator
2. **client** - Client company user
3. **forwarder** - Forwarder company user

### Permissions Matrix:

| Endpoint | super_admin | client | forwarder |
|----------|-------------|--------|-----------|
| POST /auth/login | ✅ | ✅ | ✅ |
| GET /auth/me | ✅ | ✅ | ✅ |
| GET /companies | ✅ | ❌ | ❌ |
| POST /companies | ✅ | ❌ | ❌ |
| GET /masters/* | ✅ | ✅ | ✅ |
| GET /charges | ✅ | ✅ (own) | ❌ |
| POST /charges | ✅ | ✅ (own) | ❌ |
| GET /quotes | ✅ | ✅ (own) | ✅ (own) |
| POST /quotes | ✅ | ❌ | ✅ |
| PATCH /quotes/*/status | ✅ | ✅ (buyer) | ❌ |
| GET /invoices | ✅ | ✅ (own) | ✅ (own) |
| POST /invoices/upload | ✅ | ❌ | ✅ |
| POST /invoices/*/analyze | ✅ | ✅ (buyer) | ❌ |
| POST /copilot/query | ✅ | ✅ | ❌ |

---

## Data Isolation

**Multi-Tenant Rules:**
- Users can only access data for their own company
- Super admin can access all data
- Quotes: Forwarder sees their submitted quotes, Client sees quotes for them
- Invoices: Forwarder sees their uploaded invoices, Client sees invoices for their quotes
- Charges: Scoped to company_id
- Anomalies: Only visible to client (buyer)

---

## Testing the API

Use this curl command template:

```bash
# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"client.admin@acmeco.dev","password":"TestPass123!"}'

# Use token
curl -X GET http://localhost:8001/quotes \
  -H "Authorization: Bearer <token>"
```

---

## Frontend Dependencies

The frontend only depends on:
1. **Backend API** (this contract)
2. **Node.js 18+** (for development)
3. **Modern browser** (Chrome, Firefox, Safari, Edge)

No external services required!
