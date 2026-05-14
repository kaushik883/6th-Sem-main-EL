# LogiSight - Freight Audit Platform

A freight audit and invoice analysis platform for comparing quotes vs invoices and detecting discrepancies.

## 🎯 What This Is

**LogiSight** helps freight companies and their clients:
- Submit and review freight quotes
- Upload and analyze invoices
- Detect discrepancies between quotes and invoices
- Manage standardized charge names
- Track shipments
- Query data using AI

## 📦 Project Structure

```
LogiSight/
├── frontend/              # Pure frontend (React + TypeScript)
│   ├── src/              # Source code
│   ├── API_CONTRACT.md   # Backend API specification
│   └── README.md         # Frontend documentation
│
└── .kiro/specs/          # Backend rebuild specification
    └── backend-rebuild/
        └── requirements.md
```

## 🏗️ Architecture

### Current State:
- ✅ **Frontend**: Complete, independent, ready to use
- ❌ **Backend**: Removed - needs to be rebuilt

### Frontend → Backend Communication:
```
Frontend (React)
    ↓ HTTP/JSON
Backend API (Your choice of tech stack)
    ↓
Database (Your choice: PostgreSQL, MySQL, SQLite, etc.)
```

## 🎭 User Roles

1. **Super Admin** - Platform administrator
   - Manages all companies
   - Full access to everything

2. **Client** (Buyer company)
   - **Admin**: Manages charge master, users
   - **User**: Views quotes/invoices
   - Both can: Accept/reject quotes, analyze invoices

3. **Forwarder** (Freight company)
   - **Admin**: Manages users
   - **User**: Regular operations
   - Both can: Submit quotes, upload invoices

## ✨ Features

### 1. Authentication & Access Control
- Login with email/password
- JWT token-based authentication
- Role-based access control
- Multi-tenant data isolation

### 2. Company Management (Super Admin)
- Create client and forwarder companies
- Create admin users for companies
- Activate/deactivate companies

### 3. Charge Master (Client)
**Problem**: Different freight companies use different names for the same charges
- "Air Freight" vs "Airfreight" vs "Air Transport"
- "Fuel Surcharge" vs "FSC" vs "Bunker Adjustment Factor"

**Solution**: Charge Master
- Standardized charge names per company
- Aliases for variations
- Used for automatic mapping

### 4. Quote Management

**Flow**:
1. **Forwarder submits quote** with charges
2. **System attempts automatic mapping** to client's charge master
3. **Client reviews quote** and can correct mappings
4. **Client accepts or rejects** quote

**Charge Mapping**:
- Dictionary match (exact name or alias)
- Vector similarity (fuzzy match)
- LLM fallback (complex cases)
- Human correction (manual override)

### 5. Invoice Management

**Flow**:
1. **Forwarder uploads invoice PDF** for accepted quote
2. **System extracts charges** (OCR or manual entry)
3. **System maps charges** to client's charge master
4. **Client can correct mappings**

### 6. Anomaly Detection

**Problem**: Invoices often differ from accepted quotes

**Solution**: Automated comparison
- Click "Analyze Invoice" button
- System compares invoice vs quote
- Detects 6 types of anomalies:

1. **AMOUNT_MISMATCH**: Invoiced amount ≠ quoted amount
   - Example: Quoted $100, invoiced $120

2. **RATE_MISMATCH**: Rate changed
   - Example: Quoted $5/kg, invoiced $6/kg

3. **BASIS_MISMATCH**: Calculation basis changed
   - Example: Quoted "Per KG", invoiced "Per Shipment"

4. **UNEXPECTED_CHARGE**: Charge not in quote
   - Example: "Handling Fee" appears in invoice but not in quote

5. **MISSING_CHARGE**: Charge in quote but not in invoice
   - Example: "Insurance" was quoted but not invoiced

6. **DUPLICATE_INVOICE**: Multiple invoices for same quote
   - Example: Same quote invoiced twice

**Output**:
- List of anomalies with descriptions
- Variance amounts (over/under charged)
- Total invoice vs total quote comparison

### 7. Shipment Tracking
- Track shipment status
- View tracking events timeline
- Current location and status

### 8. AI Copilot (Client)
- Ask natural language questions
- "How many quotes are pending?"
- "What's the total value of accepted quotes this month?"
- "Show me invoices with anomalies"

### 9. Dashboard
- Open quotes count
- Invoices this month
- Total accepted quotes
- Pending anomalies

## 🔄 Typical Workflow

```
1. Forwarder submits quote
   ↓
2. Client reviews and accepts quote
   ↓
3. Forwarder ships goods
   ↓
4. Forwarder uploads invoice
   ↓
5. Client analyzes invoice
   ↓
6. System detects anomalies
   ↓
7. Client reviews discrepancies
   ↓
8. Client approves or disputes invoice
```

## 🚀 Getting Started

### Frontend (Ready to Use)
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

See `frontend/README.md` for details.

### Backend (Needs to be Built)

**What you need to build:**
- Authentication system (JWT)
- 40+ API endpoints
- Database schema (12 tables)
- Business logic for each feature

**How to build:**
1. Read `frontend/API_CONTRACT.md` - Complete API specification
2. Read `.kiro/specs/backend-rebuild/requirements.md` - Detailed requirements
3. Choose your tech stack (Python/FastAPI, Node/Express, Go, etc.)
4. Choose your database (PostgreSQL, MySQL, SQLite, etc.)
5. Build feature by feature, testing against frontend

**Recommended approach:**
- Build one feature at a time
- Test each feature with the frontend before moving on
- Use AI agents to build individual features

## 📋 Backend API Contract

The frontend expects these endpoints (see `frontend/API_CONTRACT.md` for complete details):

### Authentication
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user

### Core Features
- `/companies` - Company management
- `/masters/airports`, `/masters/currencies` - Master data
- `/charges` - Charge master
- `/quotes` - Quote management
- `/invoices` - Invoice management
- `/invoices/{id}/analyze` - **Anomaly detection** (key feature!)
- `/tracking` - Shipment tracking
- `/copilot/query` - AI assistant
- `/dashboard/stats` - Dashboard

## 🎯 Key Business Logic

### Charge Mapping Algorithm
```
1. Try exact match (charge name or alias)
2. If no match, try fuzzy match (similarity score)
3. If low confidence, flag for human review
4. Human can correct mapping
5. Correction adds new alias for future
```

### Anomaly Detection Algorithm
```
For each invoice charge:
  - Find matching quote charge (by mapped_charge_id)
  - If no match → UNEXPECTED_CHARGE
  - If match:
    - Compare amounts → AMOUNT_MISMATCH
    - Compare rates → RATE_MISMATCH
    - Compare basis → BASIS_MISMATCH

For each quote charge:
  - Check if in invoice
  - If missing → MISSING_CHARGE

Check for duplicate invoices:
  - Query invoices with same quote_id
  - If multiple → DUPLICATE_INVOICE
```

## 📊 Data Models

### Key Entities:
- **Company** - Client or forwarder organization
- **User** - Person with role and company
- **Charge** - Standardized charge name (per company)
- **Quote** - Freight quote with line items
- **Invoice** - Uploaded invoice with line items
- **Anomaly** - Detected discrepancy
- **Tracking Event** - Shipment status update

### Relationships:
- User belongs to Company
- Charge belongs to Company (client only)
- Quote has Forwarder and Buyer (both companies)
- Invoice belongs to Quote
- Anomaly belongs to Invoice

See `frontend/src/api/types.ts` for complete TypeScript definitions.

## 🔐 Security & Multi-Tenancy

### Authentication:
- JWT tokens with user claims (id, role, company_id)
- Token stored in localStorage (frontend)
- Token sent in Authorization header

### Authorization:
- Role-based access control
- Company-based data isolation
- Super admin can access all data
- Users can only access their company's data

### Data Isolation:
- Quotes: Forwarder sees their quotes, Client sees quotes for them
- Invoices: Forwarder sees their invoices, Client sees invoices for their quotes
- Charges: Scoped to company_id
- Anomalies: Only visible to client (buyer)

## 📚 Documentation

- `README.md` (this file) - Overview and features
- `frontend/README.md` - Frontend documentation
- `frontend/API_CONTRACT.md` - Complete API specification
- `.kiro/specs/backend-rebuild/requirements.md` - Detailed backend requirements

## 🎨 Tech Stack

### Frontend (Implemented):
- React 18
- TypeScript
- React Router
- TanStack Query
- Axios
- Tailwind CSS
- React Hook Form + Zod

### Backend (Your Choice):
- **Language**: Python, Node.js, Go, Java, etc.
- **Framework**: FastAPI, Express, Gin, Spring Boot, etc.
- **Database**: PostgreSQL, MySQL, SQLite, etc.
- **ORM**: SQLAlchemy, Prisma, GORM, etc.

## 💡 Development Tips

### For Building Backend:
1. Start with authentication (`POST /auth/login`)
2. Test login page works
3. Build one feature at a time
4. Test each feature with frontend
5. Use the frontend as your specification

### For Using AI Agents:
1. Give agent the `frontend/API_CONTRACT.md`
2. Ask to build one feature at a time
3. Test each feature before moving on
4. Frontend will tell you if API is correct!

### For Testing:
1. Frontend will show errors if API doesn't match contract
2. Check browser console for API errors
3. Check network tab for request/response
4. Use Postman/curl to test endpoints directly

## 🐛 Common Issues

### Frontend shows "Network Error":
- Backend not running
- Wrong `VITE_API_URL` in `frontend/.env`
- CORS not configured on backend

### Login doesn't work:
- Check `/auth/login` endpoint returns correct format
- Check JWT token is being stored
- Check token is sent in Authorization header

### Data not showing:
- Check authentication (401 errors)
- Check authorization (403 errors)
- Check data isolation (company_id filtering)

## 📞 Next Steps

1. **Review features** - Understand what the system does
2. **Read API contract** - `frontend/API_CONTRACT.md`
3. **Choose tech stack** - Pick your tools
4. **Build backend** - Feature by feature
5. **Test with frontend** - Verify each feature works

---

**Built for clean architecture and developer experience** 🚀
