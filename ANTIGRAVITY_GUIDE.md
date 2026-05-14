# Complete Feature Guide for Antigravity

This document contains **everything** Antigravity needs to build a proper backend with correct user flows, validation, edge cases, and business logic.

---

## 📚 Documentation Structure

### Core Documents (Read These First)
1. **`README.md`** - Feature overview and business logic
2. **`frontend/API_CONTRACT.md`** - Complete API specification (40+ endpoints)
3. **`frontend/src/api/types.ts`** - TypeScript data models
4. **`database_schema.sql`** - Complete database schema
5. **`.kiro/specs/backend-rebuild/requirements.md`** - Detailed requirements
6. **This file** - User flows, validation rules, edge cases

---

## 🎭 User Roles & Permissions

### Role Matrix

| Feature | Super Admin | Client Admin | Client User | Forwarder Admin | Forwarder User |
|---------|-------------|--------------|-------------|-----------------|----------------|
| **Company Management** |
| Create company | ✅ | ❌ | ❌ | ❌ | ❌ |
| View all companies | ✅ | ❌ | ❌ | ❌ | ❌ |
| Activate/deactivate company | ✅ | ❌ | ❌ | ❌ | ❌ |
| Edit own company | ❌ | ✅ | ❌ | ✅ | ❌ |
| **User Management** |
| Add users to own company | ❌ | ✅ | ❌ | ✅ | ❌ |
| Promote users to admin | ❌ | ✅ | ❌ | ✅ | ❌ |
| **Charge Master** |
| View charges | ✅ | ✅ | ✅ | ❌ | ❌ |
| Create/edit charges | ❌ | ✅ | ❌ | ❌ | ❌ |
| Add/remove aliases | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Quotes** |
| View own quotes | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit quote | ❌ | ❌ | ❌ | ✅ | ✅ |
| Accept/reject quote | ❌ | ✅ | ✅ | ❌ | ❌ |
| Correct charge mapping | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Invoices** |
| View own invoices | ✅ | ✅ | ✅ | ✅ | ✅ |
| Upload invoice | ❌ | ❌ | ❌ | ✅ | ✅ |
| Analyze invoice | ❌ | ✅ | ✅ | ❌ | ❌ |
| Correct charge mapping | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Tracking** |
| View tracking | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Copilot** |
| Ask questions | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Dashboard** |
| View stats | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🔄 Complete User Flows

### Flow 1: Super Admin Creates Company

**Actors**: Super Admin

**Steps**:
1. Super admin logs in
2. Navigates to Companies page
3. Clicks "Create Company"
4. Fills form:
   - Company name (e.g., "Acme Corporation")
   - Short name (e.g., "ACME")
   - Type: Client or Forwarder
   - Address, city, zipcode, country
   - Admin user details:
     - Name (e.g., "John Doe")
     - Email (e.g., "john@acme.com")
     - Password
5. Clicks "Create"

**Backend Logic**:
```python
1. Validate company name is unique
2. Validate short name is unique
3. Validate email is unique
4. Hash password
5. Create company record (is_active=TRUE)
6. Create user record (role=client/forwarder, is_admin=TRUE, company_id=company.id)
7. Return company with admin user
```

**Validation Rules**:
- Company name: Required, 3-255 chars, unique
- Short name: Required, 2-50 chars, unique, uppercase
- Type: Required, must be 'client' or 'forwarder'
- Email: Required, valid email format, unique
- Password: Required, min 8 chars, must have uppercase, lowercase, number

**Edge Cases**:
- Duplicate company name → 400 "Company name already exists"
- Duplicate email → 400 "Email already in use"
- Invalid email format → 400 "Invalid email format"

---

### Flow 2: Forwarder Submits Quote

**Actors**: Forwarder (Admin or User)

**Steps**:
1. Forwarder logs in
2. Navigates to Quotes page
3. Clicks "Create Quote"
4. Fills form:
   - Select buyer company (dropdown of active client companies)
   - Select origin country → origin airport
   - Select destination country → destination airport
   - Enter tracking number (AWB)
   - Enter sender name & address
   - Enter receiver name & address
   - Enter number of packages
   - Enter gross weight (kg)
   - Enter volumetric weight (kg)
   - Chargeable weight auto-calculated
   - Select currency
   - Add charges (at least 1):
     - Select charge name (from forwarder's charge master)
     - Enter rate
     - Select basis (Per KG, Per Shipment, Per CBM)
     - Qty auto-calculated based on basis
     - Amount auto-calculated (rate × qty)
5. Clicks "Submit Quote"

**Backend Logic**:
```python
1. Validate user is forwarder
2. Validate buyer_id is a client company
3. Validate buyer_id ≠ forwarder_id
4. Generate quote_ref: "{ForwarderShortName}-{YYYY}-{AutoIncrement}"
   Example: "DHL-2025-00001"
5. Calculate chargeable_weight = MAX(gross_weight, volumetric_weight)
6. Set status = 'SUBMITTED'
7. Set quote_date = today
8. Create quote record
9. For each charge:
   a. Attempt charge mapping to buyer's charge master:
      - Try exact match on charge name
      - Try match on charge aliases
      - If match found:
        - Set mapped_charge_id
        - Set mapping_tier = 'DICTIONARY'
        - Set similarity_score = 1.0
        - Set low_confidence = FALSE
      - If no match:
        - Set mapped_charge_id = NULL
        - Set mapping_tier = 'UNMAPPED'
        - Set low_confidence = TRUE
   b. Calculate qty based on basis:
      - 'Per Shipment' → qty = 1
      - 'Per KG' → qty = chargeable_weight
      - 'Per CBM' → qty = volumetric_weight / 1000
   c. Calculate amount = rate × qty
   d. Create quote_charge record
10. Return complete quote with charges
```

**Validation Rules**:
- buyer_id: Required, must be active client company
- origin_airport_id: Required, must be active airport
- destination_airport_id: Required, must be active airport
- tracking_number: Required, 5-100 chars
- gross_weight: Required, > 0
- volumetric_weight: Required, > 0
- currency_id: Required, must be active currency
- charges: Required, at least 1 charge
- Each charge:
  - raw_charge_name: Required, 1-255 chars
  - rate: Required, > 0
  - basis: Required, must be 'Per KG', 'Per Shipment', or 'Per CBM'
  - amount: Required, > 0

**Edge Cases**:
- Non-forwarder tries to create → 403 "Only forwarders can create quotes"
- Buyer is forwarder company → 400 "Buyer must be a client company"
- Buyer is same as forwarder → 400 "Cannot create quote for own company"
- No charges added → 400 "At least one charge is required"
- Duplicate tracking number → Allow (multiple quotes can have same AWB)

---

### Flow 3: Client Reviews and Accepts Quote

**Actors**: Client (Admin or User)

**Steps**:
1. Client logs in
2. Navigates to Quotes page
3. Sees list of quotes where buyer_id = client's company
4. Clicks on a quote with status='SUBMITTED'
5. Reviews quote details:
   - Shipment info
   - Charges with mapping status
   - Charges with low_confidence flagged for review
6. (Optional) Corrects charge mappings:
   - Clicks "Correct Mapping" on a charge
   - Selects correct charge from dropdown
   - Saves
7. Clicks "Accept Quote" or "Reject Quote"
8. If rejecting, enters rejection note

**Backend Logic**:

**For Correcting Mapping**:
```python
1. Validate user is client
2. Validate quote belongs to user's company (buyer_id = user.company_id)
3. Validate mapped_charge_id belongs to user's company
4. Update quote_charge:
   - Set mapped_charge_id = new_charge_id
   - Set mapped_charge_name = new_charge.name
   - Set mapping_tier = 'HUMAN'
   - Set low_confidence = FALSE
5. Add raw_charge_name as alias to the charge:
   - Check if alias already exists
   - If not, create charge_alias record
6. Return success
```

**For Accept/Reject**:
```python
1. Validate user is client
2. Validate quote belongs to user's company (buyer_id = user.company_id)
3. Validate current status = 'SUBMITTED'
4. Update quote:
   - Set status = 'ACCEPTED' or 'REJECTED'
   - If rejecting, set rejection_note
   - Set updated_at = now
5. Return updated quote
```

**Validation Rules**:
- status: Required, must be 'ACCEPTED' or 'REJECTED'
- rejection_note: Required if status='REJECTED', max 1000 chars

**Edge Cases**:
- Non-client tries to accept → 403 "Only clients can accept/reject quotes"
- Quote not for user's company → 403 "Access denied"
- Quote already accepted/rejected → 400 "Quote already processed"
- Reject without note → 400 "Rejection note is required"

---

### Flow 4: Forwarder Uploads Invoice

**Actors**: Forwarder (Admin or User)

**Steps**:
1. Forwarder logs in
2. Navigates to Invoices page
3. Clicks "Upload Invoice"
4. Selects quote (dropdown shows only ACCEPTED quotes from forwarder)
5. Uploads PDF file
6. System extracts charges from PDF using Veryfi API
7. Reviews extracted charges (can correct if needed)
8. Clicks "Submit"

**Backend Logic**:
```python
1. Validate user is forwarder
2. Validate quote exists and forwarder_id = user.company_id
3. Validate quote status = 'ACCEPTED'
4. Validate file is PDF, size < 10MB
5. Store PDF file temporarily
6. Send PDF to Veryfi API for extraction:
   - Extract invoice_number, invoice_date
   - Extract line_items (charges)
7. Parse Veryfi response:
   - For each line_item:
     a. Extract: description (charge_name), unit_price (rate), quantity (qty), total (amount)
     b. Determine basis (Per KG, Per Shipment, Per CBM) - may need logic
     c. Attempt charge mapping to buyer's charge master (same logic as quote)
     d. Create invoice_charge record
8. Store PDF permanently (local filesystem or cloud)
9. Create invoice record with extracted invoice_number and invoice_date
10. Return complete invoice with charges

# Veryfi API Setup:
# pip install veryfi
# Environment variables: VERYFI_CLIENT_ID, VERYFI_CLIENT_SECRET, VERYFI_USERNAME, VERYFI_API_KEY
# Free tier: 100 documents/month
# Paid: ~$0.50-$1 per document
```

**Validation Rules**:
- quote_id: Required, must be ACCEPTED quote
- file: Required, must be PDF, max 10MB
- invoice_date: Required, valid date
- charges: Required, at least 1 charge

**Edge Cases**:
- Non-forwarder tries to upload → 403 "Only forwarders can upload invoices"
- Quote not for user's company → 403 "Access denied"
- Quote not accepted → 400 "Can only upload invoice for accepted quotes"
- Invalid file type → 400 "Only PDF files allowed"
- File too large → 400 "File size exceeds 10MB limit"
- Multiple invoices for same quote → Allow (legitimate use case)

---

### Flow 5: Client Analyzes Invoice (Anomaly Detection)

**Actors**: Client (Admin or User)

**Steps**:
1. Client logs in
2. Navigates to Invoices page
3. Clicks on an invoice
4. Reviews invoice charges
5. Clicks "Analyze Invoice" button
6. System compares invoice vs quote
7. System displays anomalies with descriptions

**Backend Logic** (CRITICAL - This is the core feature):
```python
def analyze_invoice(invoice_id, user):
    # 1. Validate access
    invoice = get_invoice(invoice_id)
    quote = invoice.quote
    if quote.buyer_id != user.company_id:
        raise Forbidden("Access denied")
    
    # 2. Get invoice charges and quote charges
    invoice_charges = get_invoice_charges(invoice_id)
    quote_charges = get_quote_charges(quote.id)
    
    # 3. Delete old anomalies for this invoice
    delete_anomalies(invoice_id)
    
    anomalies = []
    
    # 4. Compare each invoice charge against quote
    for inv_charge in invoice_charges:
        if not inv_charge.mapped_charge_id:
            # Unmapped charge - skip comparison
            continue
        
        # Find matching quote charge by mapped_charge_id
        quote_charge = find_quote_charge_by_mapped_id(
            quote_charges, 
            inv_charge.mapped_charge_id
        )
        
        if not quote_charge:
            # Charge in invoice but not in quote
            anomalies.append({
                'invoice_charge_id': inv_charge.id,
                'flag_type': 'UNEXPECTED_CHARGE',
                'description': f"Charge '{inv_charge.mapped_charge_name}' appears in invoice but was not in the quote",
                'variance': inv_charge.amount
            })
            continue
        
        # Compare amounts
        if abs(inv_charge.amount - quote_charge.amount) > 0.01:
            variance = inv_charge.amount - quote_charge.amount
            anomalies.append({
                'invoice_charge_id': inv_charge.id,
                'flag_type': 'AMOUNT_MISMATCH',
                'description': f"Amount mismatch for '{inv_charge.mapped_charge_name}': Quoted {quote_charge.amount}, Invoiced {inv_charge.amount}",
                'variance': variance
            })
        
        # Compare rates
        if abs(inv_charge.rate - quote_charge.rate) > 0.01:
            anomalies.append({
                'invoice_charge_id': inv_charge.id,
                'flag_type': 'RATE_MISMATCH',
                'description': f"Rate mismatch for '{inv_charge.mapped_charge_name}': Quoted {quote_charge.rate}, Invoiced {inv_charge.rate}",
                'variance': None
            })
        
        # Compare basis
        if inv_charge.basis != quote_charge.basis:
            anomalies.append({
                'invoice_charge_id': inv_charge.id,
                'flag_type': 'BASIS_MISMATCH',
                'description': f"Basis mismatch for '{inv_charge.mapped_charge_name}': Quoted '{quote_charge.basis}', Invoiced '{inv_charge.basis}'",
                'variance': None
            })
    
    # 5. Check for missing charges (in quote but not in invoice)
    for quote_charge in quote_charges:
        if not quote_charge.mapped_charge_id:
            continue
        
        invoice_charge = find_invoice_charge_by_mapped_id(
            invoice_charges,
            quote_charge.mapped_charge_id
        )
        
        if not invoice_charge:
            anomalies.append({
                'invoice_charge_id': None,
                'flag_type': 'MISSING_CHARGE',
                'description': f"Charge '{quote_charge.mapped_charge_name}' was quoted but not invoiced",
                'variance': -quote_charge.amount
            })
    
    # 6. Check for duplicate invoices
    other_invoices = get_invoices_for_quote(quote.id, exclude=invoice_id)
    if len(other_invoices) > 0:
        anomalies.append({
            'invoice_charge_id': None,
            'flag_type': 'DUPLICATE_INVOICE',
            'description': f"Multiple invoices found for quote {quote.quote_ref}",
            'variance': None
        })
    
    # 7. Save anomalies to database
    for anomaly_data in anomalies:
        create_anomaly(invoice_id, anomaly_data)
    
    # 8. Return anomalies
    return anomalies
```

**Validation Rules**:
- User must be client
- Invoice must belong to user's company (via quote.buyer_id)

**Edge Cases**:
- No mapped charges → Return empty anomalies list
- All charges match perfectly → Return empty anomalies list
- Multiple anomalies for same charge → Create separate anomaly records
- Re-analyze invoice → Delete old anomalies, create new ones

---

### Flow 6: Client Admin Manages Charge Master

**Actors**: Client Admin

**Steps**:
1. Client admin logs in
2. Navigates to Charge Master page
3. Sees list of company's charges
4. Can:
   - Create new charge
   - Edit charge name/short name
   - Deactivate charge (soft delete)
   - Add aliases to charge
   - Remove aliases

**Backend Logic**:

**Create Charge**:
```python
1. Validate user is client admin
2. Validate name is unique within company
3. Validate short_name is unique within company
4. Create charge record (company_id = user.company_id, is_active=TRUE)
5. Return charge
```

**Add Alias**:
```python
1. Validate user is client admin
2. Validate charge belongs to user's company
3. Validate alias doesn't already exist for this charge
4. Create charge_alias record
5. Return alias
```

**Validation Rules**:
- name: Required, 3-255 chars, unique within company
- short_name: Required, 2-50 chars, unique within company
- alias: Required, 1-255 chars, unique for this charge

**Edge Cases**:
- Duplicate charge name → 400 "Charge name already exists"
- Non-admin tries to create → 403 "Only admins can manage charges"
- Forwarder tries to access → 403 "Charge master is for clients only"

---

## 🔐 Security & Data Isolation

### Authentication
```python
def get_current_user(token: str):
    # 1. Decode JWT token
    payload = jwt.decode(token, SECRET_KEY)
    
    # 2. Extract user_id
    user_id = payload.get('user_id')
    
    # 3. Query database
    user = db.query(Profile).filter(Profile.id == user_id).first()
    
    # 4. Check user is active
    if not user.is_active:
        raise Unauthorized("User is deactivated")
    
    # 5. Check company is active
    if user.company and not user.company.is_active:
        raise Unauthorized("Company is deactivated")
    
    return user
```

### Data Isolation Rules

**Quotes**:
```python
# Forwarder sees only their quotes
if user.role == 'forwarder':
    quotes = db.query(Quote).filter(Quote.forwarder_id == user.company_id)

# Client sees only quotes for them
if user.role == 'client':
    quotes = db.query(Quote).filter(Quote.buyer_id == user.company_id)

# Super admin sees all
if user.role == 'super_admin':
    quotes = db.query(Quote).all()
```

**Invoices**:
```python
# Forwarder sees only their invoices
if user.role == 'forwarder':
    invoices = db.query(Invoice).join(Quote).filter(Quote.forwarder_id == user.company_id)

# Client sees only invoices for their quotes
if user.role == 'client':
    invoices = db.query(Invoice).join(Quote).filter(Quote.buyer_id == user.company_id)
```

**Charges**:
```python
# Only clients have charges
if user.role != 'client':
    raise Forbidden("Charge master is for clients only")

# Users see only their company's charges
charges = db.query(Charge).filter(Charge.company_id == user.company_id)
```

---

## ✅ Validation Rules Summary

### Global Rules
- All IDs must be positive integers
- All amounts must be >= 0
- All dates must be valid ISO format
- All foreign keys must reference active records (unless specified)

### Field-Specific Rules
- **Email**: Valid email format, unique across platform
- **Password**: Min 8 chars, must have uppercase, lowercase, number
- **Company name**: 3-255 chars, unique
- **Short name**: 2-50 chars, unique, uppercase recommended
- **Tracking number**: 5-100 chars
- **Weights**: > 0, decimal(10,2)
- **Rates**: > 0, decimal(10,2)
- **Amounts**: >= 0, decimal(10,2)

---

## 🐛 Error Handling

### HTTP Status Codes
- **200 OK**: Successful GET/PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Validation error
- **401 Unauthorized**: Not authenticated
- **403 Forbidden**: Not authorized
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-friendly error message",
    "details": {
      "field": "Specific error details"
    }
  }
}
```

---

## 📝 Summary for Antigravity

**When building each feature, ensure:**

1. ✅ **Authentication**: All endpoints check JWT token
2. ✅ **Authorization**: Role-based access control enforced
3. ✅ **Data Isolation**: Users see only their company's data
4. ✅ **Validation**: All inputs validated per rules above
5. ✅ **Error Handling**: Proper HTTP codes and error messages
6. ✅ **Business Logic**: Follows flows described above
7. ✅ **Edge Cases**: Handles all edge cases listed
8. ✅ **Database Constraints**: Respects foreign keys, unique constraints
9. ✅ **Soft Deletes**: Use is_active flag, never hard delete
10. ✅ **Timestamps**: Auto-update created_at, updated_at

**Test each feature with frontend before moving to next!**

---

**This guide + API_CONTRACT.md + database_schema.sql = Everything Antigravity needs!** 🚀
