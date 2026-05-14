# Next Steps - Backend Rebuild Action Plan

## 🎯 Goal
Build a production-ready backend for FreightAudit Pro using Antigravity (agentic AI), with the frontend as the specification.

---

## 📋 Decision Summary

### ✅ Decisions Made
1. **Database**: Neon PostgreSQL (serverless, free tier)
2. **Backend Framework**: Python + FastAPI (recommended)
3. **Build Approach**: Feature-by-feature with Antigravity
4. **Schema**: Complete (see `database_schema.sql`)

### ⏳ Decisions Pending
- [ ] Confirm database choice (Neon vs Local PostgreSQL vs SQLite)
- [ ] Confirm backend framework (FastAPI vs Express vs other)
- [ ] Antigravity setup and workflow

---

## 🚀 Phase 1: Database Setup (Day 1)

### Step 1.1: Sign up for Neon PostgreSQL
```bash
# Go to: https://neon.tech
# Sign up (free tier)
# Create new project: "freightaudit-pro"
# Get connection string
```

**Connection String Format:**
```
postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/freightaudit?sslmode=require
```

### Step 1.2: Run Database Schema
```bash
# Option A: Using psql
psql "postgresql://username:password@..." -f database_schema.sql

# Option B: Using Neon SQL Editor (web UI)
# Copy-paste database_schema.sql into SQL Editor
# Execute
```

### Step 1.3: Verify Database
```sql
-- Check tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Should see 14 tables:
-- companies, profiles, countries, currencies, airports, charges, 
-- charge_aliases, quotes, quote_charges, invoices, invoice_charges, 
-- anomalies, tracking_events, audit_logs

-- Check seed data
SELECT COUNT(*) FROM countries;  -- Should be 10
SELECT COUNT(*) FROM currencies; -- Should be 10
SELECT COUNT(*) FROM airports;   -- Should be 10

-- Check test accounts
SELECT email, role FROM profiles;
-- Should see: admin@freightaudit.com (super_admin)
--             client.admin@acme.com (client)
--             forwarder.admin@dhl.com (forwarder)
```

### Step 1.4: Save Connection String
```bash
# Create .env file for backend
echo "DATABASE_URL=postgresql://username:password@..." > backend/.env
echo "JWT_SECRET=your-secret-key-here" >> backend/.env
```

---

## 🛠️ Phase 2: Backend Project Setup (Day 1-2)

### Step 2.1: Create Backend Project Structure
```bash
mkdir backend
cd backend

# Python + FastAPI structure
mkdir -p app/{api/v1,core,models,schemas,services,repositories,utils}
touch app/__init__.py
touch app/main.py
touch app/core/{__init__.py,config.py,security.py,dependencies.py}
touch app/api/__init__.py
touch app/api/v1/{__init__.py,auth.py,companies.py,quotes.py,invoices.py}
```

**Recommended Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # Auth endpoints
│   │       ├── companies.py    # Company management
│   │       ├── charges.py      # Charge master
│   │       ├── quotes.py       # Quote management
│   │       ├── invoices.py     # Invoice management
│   │       ├── tracking.py     # Tracking
│   │       ├── copilot.py      # AI Copilot
│   │       └── dashboard.py    # Dashboard stats
│   ├── core/
│   │   ├── config.py           # Settings (env vars)
│   │   ├── security.py         # JWT, password hashing
│   │   └── dependencies.py     # DI (get_db, get_current_user)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py          # SQLAlchemy models
│   │   ├── user.py
│   │   ├── quote.py
│   │   └── ...
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── company.py          # Pydantic schemas (DTOs)
│   │   ├── user.py
│   │   ├── quote.py
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Business logic
│   │   ├── quote_service.py
│   │   ├── invoice_service.py
│   │   ├── anomaly_service.py  # Anomaly detection logic
│   │   └── ...
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── company_repo.py     # Data access layer
│   │   ├── quote_repo.py
│   │   └── ...
│   └── utils/
│       ├── __init__.py
│       ├── charge_mapper.py    # Charge mapping logic
│       └── pdf_extractor.py    # Invoice PDF extraction
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                    # Database migrations
├── requirements.txt
├── .env
└── README.md
```

### Step 2.2: Install Dependencies
```bash
# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
alembic==1.13.0
pytest==7.4.3
httpx==0.25.2
EOF

# Install
pip install -r requirements.txt
```

### Step 2.3: Create Basic FastAPI App
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FreightAudit Pro API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include routers (add as you build)
# from app.api.v1 import auth, companies, quotes, invoices
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
```

### Step 2.4: Test Backend
```bash
# Run server
uvicorn app.main:app --reload --port 8001

# Test health check
curl http://localhost:8001/health
# Should return: {"status":"ok"}
```

---

## 🔐 Phase 3: Authentication (Day 2-3)

### Step 3.1: Implement JWT Authentication
**Files to create:**
- `app/core/security.py` - JWT token creation/validation, password hashing
- `app/core/dependencies.py` - `get_current_user` dependency
- `app/api/v1/auth.py` - Login endpoint
- `app/schemas/auth.py` - Request/response models
- `app/services/auth_service.py` - Auth business logic

**Key Functions:**
```python
# security.py
def create_access_token(data: dict) -> str
def verify_password(plain: str, hashed: str) -> bool
def get_password_hash(password: str) -> str

# dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User

# auth_service.py
async def authenticate_user(email: str, password: str) -> User | None
```

### Step 3.2: Test Authentication
```bash
# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"client.admin@acme.com","password":"Test@123"}'

# Should return:
# {"token":"eyJ...", "user":{...}}

# Get current user
curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer eyJ..."

# Should return user profile
```

### Step 3.3: Test with Frontend
```bash
# Start frontend
cd frontend
npm run dev

# Open http://localhost:5173
# Try logging in with: client.admin@acme.com / Test@123
# Should successfully log in and redirect to dashboard
```

---

## 📦 Phase 4: Feature-by-Feature Build (Week 2-5)

### Build Order (Priority)

#### Week 2: Core Features
1. **Charge Master** (2-3 days)
   - GET /charges
   - POST /charges
   - PATCH /charges/{id}
   - POST /charges/{id}/aliases
   - DELETE /charges/aliases/{id}
   - Test: Charge Master page works

2. **Quote Management** (3-4 days)
   - GET /quotes
   - POST /quotes (with charge mapping)
   - GET /quotes/{id}
   - PATCH /quotes/{id}/status
   - PATCH /quotes/charges/{id}/mapping
   - Test: Quote pages work

#### Week 3: Invoice & Anomaly Detection
3. **Invoice Management** (3-4 days)
   - GET /invoices
   - POST /invoices/upload
   - GET /invoices/{id}
   - PATCH /invoices/charges/{id}/mapping
   - Test: Invoice pages work

4. **Anomaly Detection** (2-3 days)
   - POST /invoices/{id}/analyze
   - GET /invoices/{id}/anomalies
   - Implement 6 anomaly types
   - Test: Analysis button works

#### Week 4: Advanced Features
5. **Tracking** (2 days)
   - GET /tracking
   - GET /tracking/{quoteId}/events
   - Test: Tracking page works

6. **Dashboard** (1 day)
   - GET /dashboard/stats
   - Test: Dashboard shows correct metrics

7. **Company Management** (2 days)
   - GET /companies
   - POST /companies
   - PATCH /companies/{id}/status
   - Test: Super admin page works

#### Week 5: AI Copilot
8. **AI Copilot** (3-4 days)
   - POST /copilot/query
   - Implement LLM → SQL conversion
   - Test: Copilot page works

---

## 🤖 Using Antigravity for Each Feature

### Workflow for Each Feature

#### Step 1: Prepare Context
```
Give Antigravity:
1. API Contract: frontend/API_CONTRACT.md (specific endpoint)
2. Database Schema: database_schema.sql (relevant tables)
3. Frontend Types: frontend/src/api/types.ts (data models)
4. Requirements: .kiro/specs/backend-rebuild/requirements.md (feature section)
```

#### Step 2: Prompt Template
```
Build the [FEATURE_NAME] feature for FreightAudit Pro backend.

Context:
- Framework: FastAPI (Python)
- Database: PostgreSQL (SQLAlchemy async)
- Architecture: Clean architecture (routes → services → repositories)

Requirements:
[Paste relevant section from requirements.md]

API Contract:
[Paste relevant endpoints from API_CONTRACT.md]

Data Models:
[Paste relevant TypeScript interfaces from types.ts]

Database Tables:
[Paste relevant table definitions from schema.sql]

Tasks:
1. Create SQLAlchemy models (app/models/)
2. Create Pydantic schemas (app/schemas/)
3. Create repository (app/repositories/)
4. Create service with business logic (app/services/)
5. Create API routes (app/api/v1/)
6. Add proper error handling
7. Add data isolation (filter by company_id)
8. Write unit tests

Deliverables:
- All code files
- Test cases
- Example curl commands for testing
```

#### Step 3: Test with Frontend
```bash
# After Antigravity builds the feature:
1. Copy code to backend project
2. Run backend: uvicorn app.main:app --reload --port 8001
3. Run frontend: npm run dev
4. Test the feature in browser
5. Check for errors in console/network tab
6. Iterate if needed
```

---

## 📊 Progress Tracking

### Checklist

#### Phase 1: Database ✅
- [ ] Neon PostgreSQL account created
- [ ] Database created
- [ ] Schema executed
- [ ] Seed data verified
- [ ] Test accounts work

#### Phase 2: Project Setup ✅
- [ ] Backend project structure created
- [ ] Dependencies installed
- [ ] FastAPI app running
- [ ] Health check works

#### Phase 3: Authentication ✅
- [ ] JWT token creation/validation
- [ ] Login endpoint works
- [ ] Get current user works
- [ ] Frontend login page works

#### Phase 4: Features 🔄
- [ ] Charge Master (CRUD + aliases)
- [ ] Quote Management (submit, review, accept/reject)
- [ ] Charge Mapping (dictionary match)
- [ ] Invoice Management (upload, extract)
- [ ] Anomaly Detection (6 types)
- [ ] Tracking (list, events)
- [ ] Dashboard (stats)
- [ ] Company Management (super admin)
- [ ] AI Copilot (LLM queries)

---

## 🎯 Success Criteria

### Per Feature
- ✅ All API endpoints return correct data
- ✅ Frontend page works without errors
- ✅ Data isolation enforced (users see only their data)
- ✅ Error handling works (400, 401, 403, 404, 500)
- ✅ Unit tests pass

### Overall
- ✅ All 12 frontend pages work
- ✅ All 3 user roles work correctly
- ✅ No data leakage between companies
- ✅ All 6 anomaly types detected
- ✅ Test accounts work

---

## 📚 Resources

### Documentation
- `README.md` - Project overview
- `frontend/API_CONTRACT.md` - Complete API spec
- `frontend/src/api/types.ts` - Data models
- `.kiro/specs/backend-rebuild/requirements.md` - Detailed requirements
- `database_schema.sql` - Complete schema
- `DATABASE_DESIGN.md` - Schema documentation

### Frontend Reference
- `frontend/src/api/client.ts` - All API calls (shows what backend must provide)
- `frontend/src/pages/` - All pages (shows user flows)

### Test Accounts
```
Super Admin:
  Email: admin@freightaudit.com
  Password: Admin@123

Client Admin (Acme Corp):
  Email: client.admin@acme.com
  Password: Test@123

Forwarder Admin (DHL):
  Email: forwarder.admin@dhl.com
  Password: Test@123
```

---

## 🚨 Common Issues & Solutions

### Issue: Frontend shows "Network Error"
**Solution**: 
- Check backend is running on port 8001
- Check `frontend/.env` has `VITE_API_URL=http://localhost:8001`
- Check CORS is configured in FastAPI

### Issue: Login returns 401
**Solution**:
- Check password hash in database matches
- Check JWT secret is set in backend .env
- Check token format in response

### Issue: Data shows for wrong company
**Solution**:
- Check all queries filter by company_id
- Check get_current_user extracts company_id from token
- Check repository methods enforce data isolation

### Issue: Anomaly detection doesn't work
**Solution**:
- Check invoice has charges
- Check quote has charges
- Check charges are mapped (mapped_charge_id not null)
- Check anomaly detection logic compares by mapped_charge_id

---

## 💡 Tips for Success

1. **Build one feature at a time** - Don't try to build everything at once
2. **Test with frontend immediately** - Frontend will tell you if API is correct
3. **Use the frontend as spec** - If frontend expects it, backend must provide it
4. **Start simple** - Get basic CRUD working before adding complex logic
5. **Use Antigravity effectively** - Give it complete context for each feature
6. **Commit often** - Git commit after each working feature
7. **Read error messages** - Frontend console and network tab are your friends

---

## 📞 Next Actions

### Today
1. ✅ Review this document
2. ⏳ Decide on database (Neon recommended)
3. ⏳ Sign up for Neon PostgreSQL
4. ⏳ Run database schema
5. ⏳ Verify seed data

### Tomorrow
1. ⏳ Set up backend project structure
2. ⏳ Install dependencies
3. ⏳ Create basic FastAPI app
4. ⏳ Implement authentication
5. ⏳ Test login with frontend

### This Week
1. ⏳ Build Charge Master feature
2. ⏳ Build Quote Management feature
3. ⏳ Test both features with frontend

---

**Ready to start?** Let me know which database you choose and we'll proceed! 🚀
