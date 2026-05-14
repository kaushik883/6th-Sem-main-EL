"""
copilot_schema.py — Single source of truth for Copilot schema context.

Derived from the SQLAlchemy models in app/models. Update this file whenever
a model changes. The LLM is grounded on SCHEMA_CONTEXT; TABLE_ALLOWLIST is
enforced by the guardrail regardless of what the LLM produces.

SECURITY NOTES:
- profiles.password_hash is intentionally omitted from SCHEMA_CONTEXT.
- audit_logs is intentionally omitted (not queryable by copilot).
- TABLE_ALLOWLIST is the authoritative enforcement layer.
"""

# ---------------------------------------------------------------------------
# Schema context injected into the LLM system prompt
# ---------------------------------------------------------------------------
SCHEMA_CONTEXT = """
You are querying a PostgreSQL database for a freight audit SaaS platform.
Below is the complete schema of queryable tables (column: type).

TABLE: companies
  id (int PK), name (str), short_name (str), type (str: 'client'|'forwarder'),
  address_line1, address_line2, city, zipcode, country_id (int→countries),
  is_active (bool), created_at (timestamp)

TABLE: countries
  id (int PK), name (str), short_name (str), is_active (bool), created_at

TABLE: currencies
  id (int PK), name (str), short_name (str: USD/EUR/GBP etc), is_active (bool), created_at

TABLE: airports
  id (int PK), name (str), iata_code (str, 3-char), country_id (int→countries),
  is_active (bool), created_at

TABLE: profiles (USER ACCOUNTS — never return password_hash)
  id (str PK), email (str), name (str), role (str: 'super_admin'|'client'|'forwarder'),
  company_id (int→companies, nullable for super_admin), is_admin (bool),
  is_active (bool), created_at, updated_at

TABLE: charges (CHARGE MASTER — per-company charge definitions)
  id (int PK), company_id (int→companies), name (str), short_name (str),
  is_active (bool), created_at, updated_at

TABLE: charge_aliases (alternative names for charges used in mapping)
  id (int PK), charge_id (int→charges), alias (str), created_at

TABLE: quotes (freight quotes submitted by forwarders to buyers)
  id (int PK), quote_ref (str), status (str: 'SUBMITTED'|'ACCEPTED'|'REJECTED'),
  rejection_note (text), forwarder_id (int→companies), buyer_id (int→companies),
  origin_airport_id (int→airports), destination_airport_id (int→airports),
  tracking_number (str), sender_name_address (text), receiver_name_address (text),
  num_packages (int), gross_weight (numeric), volumetric_weight (numeric),
  chargeable_weight (numeric), currency_id (int→currencies),
  quote_date (date), created_at, updated_at

TABLE: quote_charges (line items on a quote)
  id (int PK), quote_id (int→quotes), raw_charge_name (str),
  mapped_charge_id (int→charges, nullable), mapped_charge_name (str),
  similarity_score (numeric 0-1), mapping_tier (str: DICTIONARY|VECTOR|LLM|HUMAN|UNMAPPED),
  low_confidence (bool), rate (numeric), basis (str: 'Per KG'|'Per Shipment'|'Per CBM'),
  qty (numeric), amount (numeric), created_at

TABLE: invoices (uploaded invoice PDFs linked to quotes)
  id (int PK), quote_id (int→quotes), invoice_number (str), invoice_date (date),
  file_path (text), uploaded_at (timestamp), created_at

TABLE: invoice_charges (extracted line items from invoice PDFs)
  id (int PK), invoice_id (int→invoices), raw_charge_name (str),
  mapped_charge_id (int→charges, nullable), mapped_charge_name (str),
  similarity_score (numeric 0-1), mapping_tier (str: DICTIONARY|VECTOR|LLM|HUMAN|UNMAPPED),
  low_confidence (bool), rate (numeric), basis (str: 'Per KG'|'Per Shipment'|'Per CBM'),
  qty (numeric), amount (numeric), created_at

TABLE: anomalies (discrepancies detected between invoice and quote)
  id (int PK), invoice_id (int→invoices), invoice_charge_id (int→invoice_charges, nullable),
  flag_type (str: 'AMOUNT_MISMATCH'|'RATE_MISMATCH'|'BASIS_MISMATCH'|
                   'UNEXPECTED_CHARGE'|'MISSING_CHARGE'|'DUPLICATE_INVOICE'),
  description (text), variance (numeric, positive=overcharged), created_at

TABLE: tracking_events (shipment status history per quote)
  id (int PK), quote_id (int→quotes), event_time (timestamp), location (str),
  status (str: e.g. 'Picked Up'|'In Transit'|'Delivered'), description (text), created_at

KEY RELATIONSHIPS:
- A quote links a forwarder company → buyer company via forwarder_id / buyer_id
- quote_charges.amount is the quoted price per line item
- invoice_charges.amount is the invoiced price per line item
- anomalies.variance = invoice amount minus quote amount (positive = overcharged)
- chargeable_weight = MAX(gross_weight, volumetric_weight)
""".strip()


# ---------------------------------------------------------------------------
# Authoritative table allowlist — enforced by the guardrail.
# The LLM is NOT trusted; this list is the ground truth.
# ---------------------------------------------------------------------------
TABLE_ALLOWLIST: frozenset[str] = frozenset({
    "companies",
    "countries",
    "currencies",
    "airports",
    "charges",
    "charge_aliases",
    "profiles",
    "quotes",
    "quote_charges",
    "invoices",
    "invoice_charges",
    "anomalies",
    "tracking_events",
})

# ---------------------------------------------------------------------------
# Columns that must never appear in a copilot query result
# ---------------------------------------------------------------------------
BLOCKED_COLUMNS: frozenset[str] = frozenset({
    "password_hash",
    "password_reset_token",
    "jwt_secret",
})

# ---------------------------------------------------------------------------
# Tables that are tenant-scoped (must include a company_id filter for clients)
# Maps table_name → the column that holds the company FK relevant to filtering
# ---------------------------------------------------------------------------
TENANT_SCOPED_TABLES: dict[str, list[str]] = {
    "quotes":          ["buyer_id", "forwarder_id"],
    "quote_charges":   [],   # scoped via quotes join
    "invoices":        [],   # scoped via quotes join
    "invoice_charges": [],   # scoped via invoices join
    "anomalies":       [],   # scoped via invoices join
    "charges":         ["company_id"],
    "charge_aliases":  [],   # scoped via charges join
    "profiles":        ["company_id"],
    "tracking_events": [],   # scoped via quotes join
}
