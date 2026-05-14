-- ============================================================================
-- FreightAudit Pro - Complete Database Schema
-- ============================================================================
-- This schema supports all features:
-- 1. User & Company Management
-- 2. Master Data (Country, Currency, Airport, Charge)
-- 3. Quote Management with Charge Mapping
-- 4. Invoice Management with Variance Analysis
-- 5. Anomaly Detection (6 types)
-- 6. Shipment Tracking
-- 7. AI Copilot
-- 8. Dashboard Analytics
-- ============================================================================

-- ============================================================================
-- 1. COMPANIES & USERS
-- ============================================================================

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    short_name VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('client', 'forwarder')),
    address_line1 TEXT,
    address_line2 TEXT,
    city VARCHAR(100),
    zipcode VARCHAR(20),
    country_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_type ON companies(type);
CREATE INDEX idx_companies_is_active ON companies(is_active);

-- Users/Profiles table
CREATE TABLE profiles (
    id VARCHAR(255) PRIMARY KEY, -- UUID from auth system
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    role VARCHAR(20) NOT NULL CHECK (role IN ('super_admin', 'client', 'forwarder')),
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_company_for_non_super_admin CHECK (
        (role = 'super_admin' AND company_id IS NULL) OR
        (role != 'super_admin' AND company_id IS NOT NULL)
    )
);

CREATE INDEX idx_profiles_email ON profiles(email);
CREATE INDEX idx_profiles_company_id ON profiles(company_id);
CREATE INDEX idx_profiles_role ON profiles(role);

-- ============================================================================
-- 2. MASTER DATA
-- ============================================================================

-- Countries
CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    short_name VARCHAR(10) NOT NULL UNIQUE, -- ISO code (e.g., IN, US)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_countries_is_active ON countries(is_active);

-- Currencies
CREATE TABLE currencies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    short_name VARCHAR(10) NOT NULL UNIQUE, -- ISO code (e.g., USD, INR)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_currencies_is_active ON currencies(is_active);

-- Airports
CREATE TABLE airports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    iata_code VARCHAR(3) NOT NULL UNIQUE, -- 3-letter code (e.g., DEL, JFK)
    country_id INTEGER NOT NULL REFERENCES countries(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_airports_country_id ON airports(country_id);
CREATE INDEX idx_airports_is_active ON airports(is_active);
CREATE INDEX idx_airports_iata_code ON airports(iata_code);

-- Charges (Company-specific charge master)
CREATE TABLE charges (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, name),
    UNIQUE(company_id, short_name)
);

CREATE INDEX idx_charges_company_id ON charges(company_id);
CREATE INDEX idx_charges_is_active ON charges(is_active);

-- Charge Aliases (for fuzzy matching)
CREATE TABLE charge_aliases (
    id SERIAL PRIMARY KEY,
    charge_id INTEGER NOT NULL REFERENCES charges(id) ON DELETE CASCADE,
    alias VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(charge_id, alias)
);

CREATE INDEX idx_charge_aliases_charge_id ON charge_aliases(charge_id);
CREATE INDEX idx_charge_aliases_alias ON charge_aliases(alias);

-- ============================================================================
-- 3. QUOTES
-- ============================================================================

CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    quote_ref VARCHAR(50) NOT NULL UNIQUE, -- Format: {ForwarderShortName}-{YYYY}-{AutoIncrement}
    status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED' CHECK (status IN ('SUBMITTED', 'ACCEPTED', 'REJECTED')),
    rejection_note TEXT,
    
    -- Companies
    forwarder_id INTEGER NOT NULL REFERENCES companies(id),
    buyer_id INTEGER NOT NULL REFERENCES companies(id),
    
    -- Shipment details
    origin_airport_id INTEGER NOT NULL REFERENCES airports(id),
    destination_airport_id INTEGER NOT NULL REFERENCES airports(id),
    tracking_number VARCHAR(100) NOT NULL, -- AWB number
    
    -- Sender/Receiver
    sender_name_address TEXT,
    receiver_name_address TEXT,
    
    -- Package details
    num_packages INTEGER,
    gross_weight DECIMAL(10, 2) NOT NULL, -- in KG
    volumetric_weight DECIMAL(10, 2) NOT NULL, -- in KG
    chargeable_weight DECIMAL(10, 2) NOT NULL, -- Greater of gross/volumetric
    
    -- Currency
    currency_id INTEGER NOT NULL REFERENCES currencies(id),
    
    -- Timestamps
    quote_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_forwarder_buyer_different CHECK (forwarder_id != buyer_id)
);

CREATE INDEX idx_quotes_forwarder_id ON quotes(forwarder_id);
CREATE INDEX idx_quotes_buyer_id ON quotes(buyer_id);
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_quotes_tracking_number ON quotes(tracking_number);
CREATE INDEX idx_quotes_quote_ref ON quotes(quote_ref);

-- Quote Charges (line items)
CREATE TABLE quote_charges (
    id SERIAL PRIMARY KEY,
    quote_id INTEGER NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    
    -- Original charge name from forwarder
    raw_charge_name VARCHAR(255) NOT NULL,
    
    -- Mapped to buyer's charge master
    mapped_charge_id INTEGER REFERENCES charges(id),
    mapped_charge_name VARCHAR(255),
    
    -- Mapping metadata
    similarity_score DECIMAL(5, 4), -- 0.0000 to 1.0000
    mapping_tier VARCHAR(20) CHECK (mapping_tier IN ('DICTIONARY', 'VECTOR', 'LLM', 'HUMAN', 'UNMAPPED')),
    low_confidence BOOLEAN DEFAULT FALSE,
    
    -- Charge details
    rate DECIMAL(10, 2) NOT NULL,
    basis VARCHAR(50) NOT NULL CHECK (basis IN ('Per KG', 'Per Shipment', 'Per CBM')),
    qty DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL, -- rate * qty
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quote_charges_quote_id ON quote_charges(quote_id);
CREATE INDEX idx_quote_charges_mapped_charge_id ON quote_charges(mapped_charge_id);
CREATE INDEX idx_quote_charges_mapping_tier ON quote_charges(mapping_tier);

-- ============================================================================
-- 4. INVOICES
-- ============================================================================

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    quote_id INTEGER NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    invoice_number VARCHAR(100) NOT NULL UNIQUE,
    invoice_date DATE NOT NULL,
    file_path TEXT NOT NULL, -- Path to PDF in storage
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoices_quote_id ON invoices(quote_id);
CREATE INDEX idx_invoices_invoice_number ON invoices(invoice_number);

-- Invoice Charges (extracted from PDF)
CREATE TABLE invoice_charges (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Original charge name from invoice PDF
    raw_charge_name VARCHAR(255) NOT NULL,
    
    -- Mapped to buyer's charge master
    mapped_charge_id INTEGER REFERENCES charges(id),
    mapped_charge_name VARCHAR(255),
    
    -- Mapping metadata
    similarity_score DECIMAL(5, 4),
    mapping_tier VARCHAR(20) CHECK (mapping_tier IN ('DICTIONARY', 'VECTOR', 'LLM', 'HUMAN', 'UNMAPPED')),
    low_confidence BOOLEAN DEFAULT FALSE,
    
    -- Charge details
    rate DECIMAL(10, 2) NOT NULL,
    basis VARCHAR(50) NOT NULL CHECK (basis IN ('Per KG', 'Per Shipment', 'Per CBM')),
    qty DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoice_charges_invoice_id ON invoice_charges(invoice_id);
CREATE INDEX idx_invoice_charges_mapped_charge_id ON invoice_charges(mapped_charge_id);

-- ============================================================================
-- 5. ANOMALIES (Variance Analysis Results)
-- ============================================================================

CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    invoice_charge_id INTEGER REFERENCES invoice_charges(id) ON DELETE SET NULL,
    
    -- Anomaly type
    flag_type VARCHAR(30) NOT NULL CHECK (flag_type IN (
        'AMOUNT_MISMATCH',
        'RATE_MISMATCH',
        'BASIS_MISMATCH',
        'UNEXPECTED_CHARGE',
        'MISSING_CHARGE',
        'DUPLICATE_INVOICE'
    )),
    
    -- Description and variance
    description TEXT NOT NULL,
    variance DECIMAL(10, 2), -- Invoice amount - Quote amount (can be negative)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomalies_invoice_id ON anomalies(invoice_id);
CREATE INDEX idx_anomalies_flag_type ON anomalies(flag_type);

-- ============================================================================
-- 6. TRACKING
-- ============================================================================

CREATE TABLE tracking_events (
    id SERIAL PRIMARY KEY,
    quote_id INTEGER NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    event_time TIMESTAMP NOT NULL,
    location VARCHAR(255),
    status VARCHAR(100) NOT NULL, -- e.g., "Picked Up", "In Transit", "Delivered"
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tracking_events_quote_id ON tracking_events(quote_id);
CREATE INDEX idx_tracking_events_event_time ON tracking_events(event_time);
CREATE INDEX idx_tracking_events_status ON tracking_events(status);

-- ============================================================================
-- 7. ADDITIONAL TABLES (Optional but useful)
-- ============================================================================

-- Audit log for important actions
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES profiles(id),
    action VARCHAR(100) NOT NULL, -- e.g., "CREATE_QUOTE", "ACCEPT_QUOTE", "ANALYZE_INVOICE"
    entity_type VARCHAR(50), -- e.g., "quote", "invoice", "company"
    entity_id INTEGER,
    details JSONB, -- Additional context
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- ============================================================================
-- 8. VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Quote summary with company names
CREATE VIEW v_quote_summary AS
SELECT 
    q.id,
    q.quote_ref,
    q.status,
    q.tracking_number,
    q.quote_date,
    f.name AS forwarder_name,
    f.short_name AS forwarder_short_name,
    b.name AS buyer_name,
    b.short_name AS buyer_short_name,
    oa.iata_code AS origin_code,
    oa.name AS origin_name,
    da.iata_code AS destination_code,
    da.name AS destination_name,
    c.short_name AS currency,
    q.chargeable_weight,
    q.created_at
FROM quotes q
JOIN companies f ON q.forwarder_id = f.id
JOIN companies b ON q.buyer_id = b.id
JOIN airports oa ON q.origin_airport_id = oa.id
JOIN airports da ON q.destination_airport_id = da.id
JOIN currencies c ON q.currency_id = c.id;

-- View: Invoice summary with quote info
CREATE VIEW v_invoice_summary AS
SELECT 
    i.id,
    i.invoice_number,
    i.invoice_date,
    i.quote_id,
    q.quote_ref,
    q.tracking_number,
    f.name AS forwarder_name,
    b.name AS buyer_name,
    i.uploaded_at
FROM invoices i
JOIN quotes q ON i.quote_id = q.id
JOIN companies f ON q.forwarder_id = f.id
JOIN companies b ON q.buyer_id = b.id;

-- View: Tracking status (latest event per quote)
CREATE VIEW v_tracking_status AS
SELECT DISTINCT ON (q.id)
    q.id AS quote_id,
    q.quote_ref,
    q.tracking_number,
    oa.iata_code AS origin,
    da.iata_code AS destination,
    te.status AS current_status,
    te.event_time AS last_event_time,
    f.name AS forwarder_name,
    b.name AS buyer_name
FROM quotes q
JOIN companies f ON q.forwarder_id = f.id
JOIN companies b ON q.buyer_id = b.id
JOIN airports oa ON q.origin_airport_id = oa.id
JOIN airports da ON q.destination_airport_id = da.id
LEFT JOIN tracking_events te ON q.id = te.quote_id
ORDER BY q.id, te.event_time DESC;

-- ============================================================================
-- 9. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_charges_updated_at BEFORE UPDATE ON charges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function: Auto-calculate chargeable weight
CREATE OR REPLACE FUNCTION calculate_chargeable_weight()
RETURNS TRIGGER AS $$
BEGIN
    NEW.chargeable_weight = GREATEST(NEW.gross_weight, NEW.volumetric_weight);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_quote_chargeable_weight BEFORE INSERT OR UPDATE ON quotes
    FOR EACH ROW EXECUTE FUNCTION calculate_chargeable_weight();

-- Function: Deactivate users when company is deactivated
CREATE OR REPLACE FUNCTION deactivate_company_users()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
        UPDATE profiles SET is_active = FALSE WHERE company_id = NEW.id;
    ELSIF NEW.is_active = TRUE AND OLD.is_active = FALSE THEN
        UPDATE profiles SET is_active = TRUE WHERE company_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER company_activation_trigger AFTER UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION deactivate_company_users();

-- ============================================================================
-- 10. SEED DATA (Master Data)
-- ============================================================================

-- Insert common countries
INSERT INTO countries (name, short_name) VALUES
    ('United States', 'US'),
    ('India', 'IN'),
    ('United Kingdom', 'GB'),
    ('China', 'CN'),
    ('Germany', 'DE'),
    ('United Arab Emirates', 'AE'),
    ('Singapore', 'SG'),
    ('Japan', 'JP'),
    ('Australia', 'AU'),
    ('Canada', 'CA');

-- Insert common currencies
INSERT INTO currencies (name, short_name) VALUES
    ('US Dollar', 'USD'),
    ('Indian Rupee', 'INR'),
    ('British Pound', 'GBP'),
    ('Euro', 'EUR'),
    ('Chinese Yuan', 'CNY'),
    ('UAE Dirham', 'AED'),
    ('Singapore Dollar', 'SGD'),
    ('Japanese Yen', 'JPY'),
    ('Australian Dollar', 'AUD'),
    ('Canadian Dollar', 'CAD');

-- Insert major airports (sample)
INSERT INTO airports (name, iata_code, country_id) VALUES
    ('Indira Gandhi International Airport', 'DEL', (SELECT id FROM countries WHERE short_name = 'IN')),
    ('Chhatrapati Shivaji Maharaj International Airport', 'BOM', (SELECT id FROM countries WHERE short_name = 'IN')),
    ('John F. Kennedy International Airport', 'JFK', (SELECT id FROM countries WHERE short_name = 'US')),
    ('Los Angeles International Airport', 'LAX', (SELECT id FROM countries WHERE short_name = 'US')),
    ('London Heathrow Airport', 'LHR', (SELECT id FROM countries WHERE short_name = 'GB')),
    ('Dubai International Airport', 'DXB', (SELECT id FROM countries WHERE short_name = 'AE')),
    ('Singapore Changi Airport', 'SIN', (SELECT id FROM countries WHERE short_name = 'SG')),
    ('Hong Kong International Airport', 'HKG', (SELECT id FROM countries WHERE short_name = 'CN')),
    ('Frankfurt Airport', 'FRA', (SELECT id FROM countries WHERE short_name = 'DE')),
    ('Tokyo Narita International Airport', 'NRT', (SELECT id FROM countries WHERE short_name = 'JP'));

-- ============================================================================
-- 11. TEST DATA (Optional - for development)
-- ============================================================================

-- Create Super Admin
INSERT INTO profiles (id, email, name, password_hash, role, is_admin) VALUES
    ('super-admin-001', 'admin@freightaudit.com', 'Super Admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0K3e', 'super_admin', TRUE);
-- Password: Admin@123

-- Create test companies
INSERT INTO companies (name, short_name, type, city, country_id) VALUES
    ('Acme Corporation', 'ACME', 'client', 'New York', (SELECT id FROM countries WHERE short_name = 'US')),
    ('DHL Express', 'DHL', 'forwarder', 'Mumbai', (SELECT id FROM countries WHERE short_name = 'IN')),
    ('FedEx International', 'FEDEX', 'forwarder', 'London', (SELECT id FROM countries WHERE short_name = 'GB'));

-- Create test users
INSERT INTO profiles (id, email, name, password_hash, role, company_id, is_admin) VALUES
    ('client-admin-001', 'client.admin@acme.com', 'John Client', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0K3e', 'client', (SELECT id FROM companies WHERE short_name = 'ACME'), TRUE),
    ('forwarder-admin-001', 'forwarder.admin@dhl.com', 'Sarah Forwarder', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0K3e', 'forwarder', (SELECT id FROM companies WHERE short_name = 'DHL'), TRUE);
-- Password: Test@123

-- Create sample charges for Acme (client)
INSERT INTO charges (company_id, name, short_name) VALUES
    ((SELECT id FROM companies WHERE short_name = 'ACME'), 'Air Freight', 'AF'),
    ((SELECT id FROM companies WHERE short_name = 'ACME'), 'Fuel Surcharge', 'FSC'),
    ((SELECT id FROM companies WHERE short_name = 'ACME'), 'Security Fee', 'SEC'),
    ((SELECT id FROM companies WHERE short_name = 'ACME'), 'Handling Charge', 'HDL'),
    ((SELECT id FROM companies WHERE short_name = 'ACME'), 'Documentation Fee', 'DOC');

-- Add aliases for fuzzy matching
INSERT INTO charge_aliases (charge_id, alias) VALUES
    ((SELECT id FROM charges WHERE name = 'Air Freight' AND company_id = (SELECT id FROM companies WHERE short_name = 'ACME')), 'Airfreight'),
    ((SELECT id FROM charges WHERE name = 'Air Freight' AND company_id = (SELECT id FROM companies WHERE short_name = 'ACME')), 'Air Transport'),
    ((SELECT id FROM charges WHERE name = 'Fuel Surcharge' AND company_id = (SELECT id FROM companies WHERE short_name = 'ACME')), 'FSC'),
    ((SELECT id FROM charges WHERE name = 'Fuel Surcharge' AND company_id = (SELECT id FROM companies WHERE short_name = 'ACME')), 'Bunker Adjustment Factor');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Summary:
-- - 13 core tables (companies, profiles, countries, currencies, airports, charges, 
--   charge_aliases, quotes, quote_charges, invoices, invoice_charges, anomalies, 
--   tracking_events)
-- - 1 audit table (audit_logs)
-- - 3 views for common queries
-- - 4 triggers for automation
-- - Seed data for countries, currencies, airports
-- - Test data for development
