# Quick Reference Card

## 📁 Files You Have

| File | Purpose |
|------|---------|
| `database_schema.sql` | Complete PostgreSQL schema (run this first) |
| `DATABASE_DESIGN.md` | Schema documentation with ERD |
| `NEXT_STEPS.md` | Detailed step-by-step action plan |
| `BRAINSTORM_SUMMARY.md` | Decision summary and recommendations |
| `QUICK_REFERENCE.md` | This file - quick lookup |

---

## 🗄️ Database Quick Facts

- **Tables**: 14 (13 core + 1 audit)
- **Views**: 3 (quote_summary, invoice_summary, tracking_status)
- **Triggers**: 4 (auto-update timestamps, calculate weights, cascade deactivation)
- **Seed Data**: 30 records (countries, currencies, airports)
- **Test Accounts**: 3 users (super admin, client admin, forwarder admin)

---

## 🔑 Test Accounts

```bash
# Super Admin
Email: admin@freightaudit.com
Password: Admin@123

# Client Admin (Acme Corp)
Email: client.admin@acme.com
Password: Test@123

# Forwarder Admin (DHL)
Email: forwarder.admin@dhl.com
Password: Test@123
```

---

## 🚀 Quick Start Commands

### 1. Database Setup (Neon)
```bash
# Sign up: https://neon.tech
# Create project: freightaudit-pro
# Get connection string

# Run schema
psql "postgresql://user:pass@host/db" -f database_schema.sql

# Verify
psql "postgresql://user:pass@host/db" -c "SELECT COUNT(*) FROM companies;"
```

### 2. Backend Setup (FastAPI)
```bash
# Create project
mkdir backend && cd backend
mkdir -p app/{api/v1,core,models,schemas,services,repositories}

# Install dependencies
pip install fastapi uvicorn sqlalchemy asyncpg pydantic python-jose passlib

# Create .env
echo "DATABASE_URL=postgresql://..." > .env
echo "JWT_SECRET=your-secret-key" >> .env

# Run server
uvicorn app.main:app --reload --port 8001
```

### 3. Frontend Setup
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8001" > .env
npm run dev
```

---

## 📊 Database Tables

### Core Tables
1. **companies** - Organizations (client/forwarder)
2. **profiles** - Users with roles
3. **countries** - Master data
4. **currencies** - Master data
5. **airports** - Master data (IATA codes)
6. **charges** - Company-specific charge master
7. **charge_aliases** - Fuzzy matching aliases

### Transaction Tables
8. **quotes** - Freight quotes (SUBMITTED/ACCEPTED/REJECTED)
9. **quote_charges** - Quote line items with mapping
10. **invoices** - Uploaded PDFs
11. **invoice_charges** - Extracted charges with mapping
12. **anomalies** - Detected discrepancies (6 types)
13. **tracking_events** - Shipment tracking history

### Audit
14. **audit_logs** - Action audit trail

---

## 🎯 Feature Build Order

### Week 1: Foundation
- [x] Database setup
- [ ] Backend project structure
- [ ] Authentication (JWT)

### Week 2: Core Features
- [ ] Charge Master (CRUD + aliases)
- [ ] Quote Management (submit, review, accept/reject)

### Week 3: Invoice & Analysis
- [ ] Invoice Management (upload, extract)
- [ ] Anomaly Detection (6 types)

### Week 4: Advanced
- [ ] Tracking (list, events)
- [ ] Dashboard (stats)
- [ ] Company Management (super admin)

### Week 5: AI
- [ ] AI Copilot (LLM queries)

---

## 🔐 API Endpoints (40+ total)

### Auth
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user

### Companies (Super Admin)
- `GET /companies` - List all
- `POST /companies` - Create with admin user
- `PATCH /companies/{id}/status` - Activate/deactivate

### Master Data
- `GET /masters/airports` - List airports
- `GET /masters/currencies` - List currencies

### Charges (Client Admin)
- `GET /charges` - List company charges
- `POST /charges` - Create charge
- `PATCH /charges/{id}` - Update charge
- `POST /charges/{id}/aliases` - Add alias
- `DELETE /charges/aliases/{id}` - Remove alias

### Quotes
- `GET /quotes` - List (filtered by role)
- `POST /quotes` - Submit (forwarder)
- `GET /quotes/{id}` - Get details
- `PATCH /quotes/{id}/status` - Accept/reject (client)
- `PATCH /quotes/charges/{id}/mapping` - Correct mapping

### Invoices
- `GET /invoices` - List (filtered by role)
- `POST /invoices/upload` - Upload PDF (forwarder)
- `GET /invoices/{id}` - Get details
- `POST /invoices/{id}/analyze` - Run analysis (client)
- `GET /invoices/{id}/anomalies` - Get anomalies
- `PATCH /invoices/charges/{id}/mapping` - Correct mapping

### Tracking
- `GET /tracking` - List shipments
- `GET /tracking/{quoteId}/events` - Get events

### Copilot
- `POST /copilot/query` - Ask question

### Dashboard
- `GET /dashboard/stats` - Get metrics

---

## 🎨 Tech Stack Recommendations

### Backend
- **Framework**: FastAPI (Python) ✨
- **Database**: Neon PostgreSQL ✨
- **ORM**: SQLAlchemy 2.0 (async)
- **Auth**: python-jose (JWT)
- **Validation**: Pydantic

### Frontend (Already Built)
- React 18 + TypeScript
- React Router 7
- TanStack Query
- Axios
- Tailwind CSS

---

## 🐛 Common Issues

### "Network Error" in Frontend
```bash
# Check backend is running
curl http://localhost:8001/health

# Check CORS in FastAPI
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"])

# Check frontend .env
cat frontend/.env
# Should have: VITE_API_URL=http://localhost:8001
```

### Login Returns 401
```bash
# Check password hash
SELECT email, password_hash FROM profiles WHERE email = 'client.admin@acme.com';

# Check JWT secret
cat backend/.env
# Should have: JWT_SECRET=your-secret-key

# Test login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"client.admin@acme.com","password":"Test@123"}'
```

### Data Shows for Wrong Company
```bash
# Check data isolation in repository
# All queries must filter by company_id

# Example (correct):
SELECT * FROM quotes WHERE buyer_id = user.company_id OR forwarder_id = user.company_id

# Example (wrong):
SELECT * FROM quotes  # No filtering!
```

---

## 📚 Documentation Locations

### Backend Spec
- **API Contract**: `frontend/API_CONTRACT.md`
- **Data Models**: `frontend/src/api/types.ts`
- **Requirements**: `.kiro/specs/backend-rebuild/requirements.md`
- **Schema**: `database_schema.sql`

### Frontend Reference
- **API Calls**: `frontend/src/api/client.ts`
- **Pages**: `frontend/src/pages/`
- **Components**: `frontend/src/components/`

### Project Docs
- **Main README**: `README.md`
- **Frontend README**: `frontend/README.md`
- **SRS Document**: (PDF you provided)

---

## 🤖 Antigravity Prompt Template

```
Build the [FEATURE_NAME] feature for FreightAudit Pro backend.

Context:
- Framework: FastAPI (Python)
- Database: PostgreSQL (SQLAlchemy async)
- Architecture: Clean architecture (routes → services → repositories)

API Contract:
[Paste from frontend/API_CONTRACT.md]

Data Models:
[Paste from frontend/src/api/types.ts]

Database Tables:
[Paste from database_schema.sql]

Requirements:
[Paste from requirements.md]

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
- Example curl commands
```

---

## ✅ Verification Checklist

### Database
- [ ] 14 tables created
- [ ] 30 seed records (countries, currencies, airports)
- [ ] 3 test users created
- [ ] Can connect from backend

### Backend
- [ ] FastAPI app runs on port 8001
- [ ] Health check works: `curl http://localhost:8001/health`
- [ ] Login works with test accounts
- [ ] JWT token returned

### Frontend
- [ ] Runs on port 5173
- [ ] Can log in with test accounts
- [ ] Dashboard loads after login
- [ ] No console errors

### Integration
- [ ] Frontend can call backend API
- [ ] CORS works
- [ ] Authentication works
- [ ] Data shows correctly

---

## 🎯 Success Criteria

### Per Feature
- ✅ API endpoints return correct data format
- ✅ Frontend page works without errors
- ✅ Data isolation enforced (users see only their data)
- ✅ Error handling works (400, 401, 403, 404, 500)
- ✅ Unit tests pass

### Overall
- ✅ All 12 frontend pages work
- ✅ All 3 user roles work correctly
- ✅ No data leakage between companies
- ✅ All 6 anomaly types detected
- ✅ Production-ready code

---

## 📞 Next Actions

1. **Choose database**: Neon PostgreSQL (recommended) or Local
2. **Run schema**: Execute `database_schema.sql`
3. **Verify data**: Check seed data and test accounts
4. **Set up backend**: Create FastAPI project
5. **Build auth**: Implement JWT authentication
6. **Test login**: Verify frontend can log in
7. **Build features**: One by one with Antigravity

---

## 💡 Pro Tips

1. **Test with frontend immediately** - Don't wait to test
2. **Use frontend as spec** - It tells you what to build
3. **Build one feature at a time** - Don't try to do everything
4. **Commit often** - Git commit after each working feature
5. **Read error messages** - Console and network tab are your friends
6. **Use Antigravity effectively** - Give it complete context
7. **Start simple** - Get basic CRUD working first

---

## 🔗 Useful Links

- **Neon PostgreSQL**: https://neon.tech
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **Pydantic Docs**: https://docs.pydantic.dev

---

**Ready to build? Start with `NEXT_STEPS.md` for detailed instructions!** 🚀
