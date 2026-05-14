# LogiSight — Backend Integration Guide

This document is the authoritative contract between the React frontend and the Python FastAPI backend.

---

## 1. Authentication Architecture

### How It Works

The frontend uses **Supabase Auth** exclusively. Users log in via `supabase.auth.signInWithPassword()`. The resulting JWT (Supabase Access Token) is automatically attached by the Axios client to every API request as:

```
Authorization: Bearer <supabase_access_token>
```

### FastAPI JWT Middleware

The FastAPI backend must verify this Supabase JWT on every protected endpoint. Supabase uses RS256 JWTs signed with the project's private key. Use the Supabase JWKS endpoint to verify:

```python
# backend/app/dependencies.py

import os
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # PyJWT

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

security = HTTPBearer()

async def get_jwks():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
        return r.json()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        jwks = await get_jwks()
        public_keys = [jwt.algorithms.RSAAlgorithm.from_jwk(k) for k in jwks["keys"]]
        # Try each key (typically only one)
        payload = None
        for key in public_keys:
            try:
                payload = jwt.decode(
                    token,
                    key=key,
                    algorithms=["RS256"],
                    audience="authenticated",
                )
                break
            except jwt.InvalidTokenError:
                continue
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Supabase puts custom claims in app_metadata and user_metadata
    app_meta = payload.get("app_metadata", {})
    user_meta = payload.get("user_metadata", {})

    return {
        "id": payload["sub"],             # Supabase user UUID
        "email": payload.get("email"),
        "role": app_meta.get("role") or user_meta.get("role"),          # 'super_admin' | 'client' | 'forwarder'
        "company_id": app_meta.get("company_id") or user_meta.get("company_id"),
        "company_type": app_meta.get("company_type") or user_meta.get("company_type"),
        "is_admin": app_meta.get("is_admin", False),
    }
```

### Setting User Metadata on Account Creation

When the Super Admin creates a company via `POST /companies`, the backend must:
1. Create the company record in Postgres
2. Create the Supabase auth user using the **Supabase Admin Client** (service role key)
3. Set `app_metadata` (not `user_metadata` — users can't modify it) with role info:

```python
from supabase import create_client

supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

supabase_admin.auth.admin.create_user({
    "email": admin_email,
    "password": admin_password,
    "app_metadata": {
        "role": "client",          # or "forwarder"
        "company_id": company.id,
        "company_type": "client",
        "company_name": company.name,
        "is_admin": True,
    },
    "email_confirm": True,         # Skip email confirmation
})
```

For Super Admins, set `"role": "super_admin"` and omit company fields.

### CORS Configuration

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-vercel-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 2. TypeScript ↔ Pydantic Schema Contracts

### Company

**TypeScript (frontend):**
```typescript
interface Company {
  id: number;
  name: string;
  short_name: string;
  type: 'client' | 'forwarder';
  address?: string;
  city?: string;
  country?: string;
  is_active: boolean;
}
```

**Pydantic (backend):**
```python
from pydantic import BaseModel
from typing import Literal, Optional

class CompanyRead(BaseModel):
    id: int
    name: str
    short_name: str
    type: Literal["client", "forwarder"]
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
```

### ChargeLineRow

**TypeScript:**
```typescript
interface ChargeLineRow {
  id: number;
  raw_charge_name: string;
  mapped_charge_id?: number | null;
  mapped_charge_name?: string | null;
  similarity_score?: number | null;
  mapping_tier: 'DICTIONARY' | 'VECTOR' | 'LLM' | 'HUMAN' | 'UNMAPPED';
  low_confidence: boolean;
  rate: number;
  basis: 'Per KG' | 'Per Shipment' | 'Per CBM';
  qty: number;
  amount: number;
}
```

**Pydantic:**
```python
from enum import Enum
from typing import Optional

class MappingTier(str, Enum):
    DICTIONARY = "DICTIONARY"
    VECTOR = "VECTOR"
    LLM = "LLM"
    HUMAN = "HUMAN"
    UNMAPPED = "UNMAPPED"

class ChargeBasis(str, Enum):
    PER_KG = "Per KG"
    PER_SHIPMENT = "Per Shipment"
    PER_CBM = "Per CBM"

class ChargeLineRead(BaseModel):
    id: int
    raw_charge_name: str
    mapped_charge_id: Optional[int] = None
    mapped_charge_name: Optional[str] = None
    similarity_score: Optional[float] = None
    mapping_tier: MappingTier
    low_confidence: bool
    rate: float
    basis: ChargeBasis
    qty: float
    amount: float

    class Config:
        from_attributes = True
```

### QuoteDetail

**TypeScript:**
```typescript
interface QuoteDetail {
  id: number;
  quote_ref: string;
  status: 'SUBMITTED' | 'ACCEPTED' | 'REJECTED';
  rejection_note?: string | null;
  created_at: string;          // ISO datetime string
  forwarder: { id: number; name: string };
  buyer: { id: number; name: string };
  origin_airport: { iata_code: string; name: string };
  destination_airport: { iata_code: string; name: string };
  tracking_number: string;
  gross_weight: number;
  volumetric_weight: number;
  chargeable_weight: number;
  currency: { short_name: string };
  charges: ChargeLineRow[];
}
```

**Pydantic:**
```python
from datetime import datetime

class CompanyRef(BaseModel):
    id: int
    name: str

class AirportRef(BaseModel):
    iata_code: str
    name: str

class CurrencyRef(BaseModel):
    short_name: str

class QuoteStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class QuoteDetailRead(BaseModel):
    id: int
    quote_ref: str
    status: QuoteStatus
    rejection_note: Optional[str] = None
    created_at: datetime
    forwarder: CompanyRef
    buyer: CompanyRef
    origin_airport: AirportRef
    destination_airport: AirportRef
    tracking_number: str
    gross_weight: float
    volumetric_weight: float
    chargeable_weight: float
    currency: CurrencyRef
    charges: list[ChargeLineRead]

    class Config:
        from_attributes = True
```

### AnomalyRead

**TypeScript:**
```typescript
interface AnomalyRead {
  id: number;
  invoice_id: number;
  invoice_charge_id: number;
  flag_type: 'AMOUNT_MISMATCH' | 'RATE_MISMATCH' | 'BASIS_MISMATCH' |
             'UNEXPECTED_CHARGE' | 'MISSING_CHARGE' | 'DUPLICATE_INVOICE';
  description: string;
  variance?: number | null;
}
```

**Pydantic:**
```python
class AnomalyFlagType(str, Enum):
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    RATE_MISMATCH = "RATE_MISMATCH"
    BASIS_MISMATCH = "BASIS_MISMATCH"
    UNEXPECTED_CHARGE = "UNEXPECTED_CHARGE"
    MISSING_CHARGE = "MISSING_CHARGE"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"

class AnomalyRead(BaseModel):
    id: int
    invoice_id: int
    invoice_charge_id: int
    flag_type: AnomalyFlagType
    description: str
    variance: Optional[float] = None

    class Config:
        from_attributes = True
```

### TrackingEvent

**TypeScript:**
```typescript
interface TrackingEvent {
  id: number;
  quote_id: number;
  event_time: string;    // ISO datetime
  location: string;
  status: string;
  description: string;
}

interface TrackingShipment {
  quote_id: number;
  quote_ref: string;
  tracking_number: string;
  origin: string;        // IATA code
  destination: string;   // IATA code
  current_status: string;
  last_event_time: string;
  forwarder_name: string;
  buyer_name: string;
}
```

**Pydantic:**
```python
class TrackingEventRead(BaseModel):
    id: int
    quote_id: int
    event_time: datetime
    location: str
    status: str
    description: str

class TrackingShipmentRead(BaseModel):
    quote_id: int
    quote_ref: str
    tracking_number: str
    origin: str
    destination: str
    current_status: str
    last_event_time: datetime
    forwarder_name: str
    buyer_name: str
```

---

## 3. Endpoint Routing Guide: Supabase Direct vs FastAPI

### Route via Supabase PostgREST directly (NOT recommended — use FastAPI for all calls)

The frontend currently routes **all data calls through FastAPI** for the following reasons:
- Company scoping (`company_id` enforcement) is applied at the FastAPI layer, not via RLS (the backend uses application-level isolation)
- The mapping pipeline, OCR, and anomaly detection are FastAPI-only capabilities
- A single API surface simplifies auth token handling

### Endpoints that MUST hit FastAPI

| Endpoint | Reason |
|---|---|
| `POST /quotes` | Triggers the three-tier mapping pipeline |
| `POST /invoices/upload` | Veryfi OCR extraction + mapping pipeline |
| `POST /invoices/{id}/analyze` | Anomaly detection engine |
| `POST /copilot/query` | LangChain SQL agent |
| `PATCH /quotes/charges/{id}/mapping` | Saves correction as new alias |
| `PATCH /invoices/charges/{id}/mapping` | Saves correction as new alias |
| All auth-scoped reads | Company_id enforcement |

### Copilot Endpoint Contract

**Request (frontend `POST /copilot/query`):**
```typescript
{ question: string }
```

**Response:**
```typescript
{ answer: string }
```

**FastAPI Pydantic:**
```python
class CopilotQueryRequest(BaseModel):
    question: str

class CopilotQueryResponse(BaseModel):
    answer: str
```

**Role Guard:** Copilot is available only to `role == "client"`. Return HTTP 403 for forwarders.

### Quote Status Update Contract

**Request (`PATCH /quotes/{id}/status`):**
```typescript
{ status: 'ACCEPTED' | 'REJECTED'; rejection_note?: string }
```

**Pydantic:**
```python
class QuoteStatusUpdate(BaseModel):
    status: QuoteStatus
    rejection_note: Optional[str] = None
```

### Invoice Upload Contract

**Request (`POST /invoices/upload`):**
- `Content-Type: multipart/form-data`
- Field `quote_id`: string (integer as string)
- Field `file`: PDF binary

**Response:** Full `InvoiceDetailRead` including extracted and mapped charge lines (preview before analysis).

### Mapping Correction Contract

**Request (`PATCH /quotes/charges/{id}/mapping` and `/invoices/charges/{id}/mapping`):**
```typescript
{ mapped_charge_id: number }
```

**Side effect:** The backend MUST automatically save the `raw_charge_name` as a new alias on the `charge_aliases` table for the resolved `mapped_charge_id`. This makes the correction permanent and feeds Tier 1 on all future submissions.

**Pydantic:**
```python
class MappingCorrectionRequest(BaseModel):
    mapped_charge_id: int
```

**Handler logic:**
```python
@router.patch("/charges/{charge_id}/mapping")
async def correct_mapping(
    charge_id: int,
    body: MappingCorrectionRequest,
    current_user = Depends(get_current_user),
):
    charge = await get_quote_charge(charge_id)  # or invoice_charge
    # Update the charge record
    charge.mapped_charge_id = body.mapped_charge_id
    charge.mapping_tier = MappingTier.HUMAN
    charge.low_confidence = False
    # Save correction as alias
    new_alias = ChargeAlias(
        charge_id=body.mapped_charge_id,
        alias=charge.raw_charge_name,
    )
    db.add(new_alias)
    await db.commit()
    return charge
```

---

## 4. Data Visibility Enforcement

The backend must enforce these visibility rules at the query level, not just the frontend:

| Data | Enforcement |
|---|---|
| Quote charge lines | When role == forwarder: return only `raw_charge_name`; null out `mapped_charge_name`, `mapped_charge_id`, `similarity_score`, `mapping_tier` |
| Charge Master | Never return to forwarder role (403 on any `/masters/charges` call) |
| Anomalies | Never return to forwarder role |
| Rejection note | Scrub any Charge Master nomenclature before returning to forwarder |
| Company data | Always scope by `company_id` from JWT |

**Example query scoping:**
```python
@router.get("/quotes")
async def list_quotes(current_user = Depends(get_current_user)):
    company_id = current_user["company_id"]
    role = current_user["role"]

    if role == "client":
        # Client sees quotes addressed to their company
        quotes = await db.execute(
            select(Quote).where(Quote.buyer_id == company_id)
        )
    elif role == "forwarder":
        # Forwarder sees only their own submitted quotes
        quotes = await db.execute(
            select(Quote).where(Quote.forwarder_id == company_id)
        )
    elif role == "super_admin":
        quotes = await db.execute(select(Quote))

    return [serialize_quote(q, role) for q in quotes.scalars()]
```

---

## 5. Environment Variables Required

### Frontend (`.env`)
```
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon_key>
VITE_API_URL=https://your-backend.railway.app
```

### Backend (`.env`)
```
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon_key>
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>   # For admin user creation
VERYFI_CLIENT_ID=...
VERYFI_CLIENT_SECRET=...
VERYFI_USERNAME=...
VERYFI_API_KEY=...
OPENAI_API_KEY=sk-...
```

---

## 6. FastAPI Router Registration

```python
# backend/app/main.py

from app.routers import auth, companies, masters, quotes, invoices, tracking, copilot

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(masters.router, prefix="/masters", tags=["masters"])
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
app.include_router(tracking.router, prefix="/tracking", tags=["tracking"])
app.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
```

---

## 7. Copilot Backend Implementation

```python
# backend/app/services/copilot.py
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
import os

def get_copilot_agent(company_id: int):
    db = SQLDatabase.from_uri(os.environ["DATABASE_URL"])
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prefix = f"""You are a freight audit assistant for a logistics company.
You have access to a PostgreSQL database. ALWAYS filter queries by company_id = {company_id}.
The user's company is a freight client. Only return data belonging to this company.
Never return data from other companies. Be concise and professional.
All charge names use standardised Charge Master nomenclature.
"""
    return create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        prefix=prefix,
        verbose=False,
    )

async def run_copilot_query(question: str, company_id: int) -> str:
    agent = get_copilot_agent(company_id)
    result = agent.invoke({"input": question})
    return result.get("output", "I could not find an answer to that question.")
```

```python
# backend/app/routers/copilot.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.services.copilot import run_copilot_query
from pydantic import BaseModel

router = APIRouter()

class CopilotQueryRequest(BaseModel):
    question: str

@router.post("/query")
async def copilot_query(
    body: CopilotQueryRequest,
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only Client users can access the Copilot")
    answer = await run_copilot_query(body.question, current_user["company_id"])
    return {"answer": answer}
```

---

## 8. `requirements.txt` Additions (Copilot)

```
langchain>=0.2.0
langchain-community>=0.2.0
langchain-openai>=0.1.0
PyJWT>=2.8.0
cryptography>=41.0.0    # For RS256 JWT verification
httpx>=0.27.0
supabase>=2.0.0
```
