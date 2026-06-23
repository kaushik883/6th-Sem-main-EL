from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
import logging
import uuid
import os
import datetime

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.invoice import Invoice, InvoiceCharge, Anomaly
from app.models.quote import Quote
from app.models.master import Charge, ChargeAlias

# Import reusable mapping logic from quotes
from app.api.v1.quotes import map_charge

# Import services
from app.services.veryfi_client import extract_invoice_data
from app.services.r2_storage import upload_file_to_r2
from app.services.ei_forensics import TelemetryForensics

_forensics = TelemetryForensics()

router = APIRouter()

# ── Schemas ────────────────────────────────────────────────────────────────────

class UpdateChargeMappingRequest(BaseModel):
    mapped_charge_id: int

# ── Helpers ────────────────────────────────────────────────────────────────────

async def build_invoice_out(invoice: Invoice, db: AsyncSession, include_charges: bool = False) -> dict:
    quote = await db.get(Quote, invoice.quote_id)

    result = {
        "id": invoice.id,
        "quote_id": invoice.quote_id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "file_path": invoice.file_path,
        "uploaded_at": invoice.uploaded_at.isoformat() if invoice.uploaded_at else None,
        "quote": {
            "id": quote.id,
            "quote_ref": quote.quote_ref,
            "tracking_number": quote.tracking_number,
        } if quote else {}
    }

    if include_charges:
        charges_result = await db.execute(select(InvoiceCharge).where(InvoiceCharge.invoice_id == invoice.id))
        charges = charges_result.scalars().all()
        result["charges"] = [
            {
                "id": c.id,
                "raw_charge_name": c.raw_charge_name,
                "mapped_charge_id": c.mapped_charge_id,
                "mapped_charge_name": c.mapped_charge_name,
                "similarity_score": float(c.similarity_score) if c.similarity_score else None,
                "mapping_tier": c.mapping_tier,
                "low_confidence": c.low_confidence,
                "rate": float(c.rate),
                "basis": c.basis,
                "qty": float(c.qty),
                "amount": float(c.amount),
            }
            for c in charges
        ]
    return result

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[dict])
async def list_invoices(
    quote_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user["role"]
    company_id = current_user["company_id"]

    q = select(Invoice).join(Quote)
    if role == "forwarder":
        q = q.where(Quote.forwarder_id == company_id)
    elif role == "client":
        q = q.where(Quote.buyer_id == company_id)

    if quote_id:
        q = q.where(Invoice.quote_id == quote_id)

    q = q.order_by(Invoice.uploaded_at.desc())
    result = await db.execute(q)
    invoices = result.scalars().all()

    return [await build_invoice_out(inv, db, include_charges=False) for inv in invoices]


@router.get("/{invoice_id}", response_model=dict)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Invoice not found"})

    quote = await db.get(Quote, invoice.quote_id)
    role = current_user["role"]
    company_id = current_user["company_id"]
    if role == "forwarder" and quote.forwarder_id != company_id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})
    if role == "client" and quote.buyer_id != company_id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    return await build_invoice_out(invoice, db, include_charges=True)


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    tracking_number: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("forwarder", "super_admin")),
):
    # Validations
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Only PDF files are allowed"})

    result = await db.execute(
        select(Quote)
        .where(Quote.tracking_number == tracking_number)
        .order_by(Quote.id.desc())
    )
    quote = result.scalars().first()
    if not quote:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Quote not found for this tracking number"})
    if quote.status != "ACCEPTED":
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Can only upload invoices for ACCEPTED quotes"})
    if current_user["role"] != "super_admin" and quote.forwarder_id != current_user["company_id"]:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    # Save PDF locally (temporarily)
    os.makedirs("uploads", exist_ok=True)
    temp_file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    file_bytes = await file.read()
    
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "File size exceeds 10MB limit"})
        
    with open(temp_file_path, "wb") as f:
        f.write(file_bytes)

    try:
        # Step 1: Veryfi Extraction
        try:
            extracted_data = await extract_invoice_data(temp_file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail={"code": "EXTRACTION_FAILED", "message": str(e)})

        if not extracted_data.get("line_items"):
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "No line items could be extracted from the invoice"})

        # Step 2: Create Invoice DB Record (without file_path initially to get ID)
        inv_date = None
        if extracted_data.get("date"):
            try:
                inv_date = datetime.date.fromisoformat(extracted_data["date"])
            except ValueError:
                inv_date = datetime.date.today()
        else:
            inv_date = datetime.date.today()
            
        inv_number = extracted_data["invoice_number"]
        
        # Check if invoice number already exists
        existing_inv = await db.execute(select(Invoice).where(Invoice.invoice_number == inv_number))
        if existing_inv.scalar_one_or_none():
            # Append a random suffix to allow uploading the same test document again
            inv_number = f"{inv_number}-{uuid.uuid4().hex[:4]}"

        invoice = Invoice(
            quote_id=quote.id,
            invoice_number=inv_number,
            invoice_date=inv_date,
            file_path="",  # Will update after R2 upload
        )
        db.add(invoice)
        await db.flush() # flush to get invoice.id

        # Step 3: R2 Upload
        object_name = f"invoices/{invoice.id}_{uuid.uuid4().hex[:8]}.pdf"
        try:
            public_url = await upload_file_to_r2(temp_file_path, object_name)
            invoice.file_path = public_url
        except Exception as e:
            raise HTTPException(status_code=500, detail={"code": "STORAGE_FAILED", "message": "Failed to upload to Cloudflare R2"})

        # Step 4: Map Charges
        buyer_id = quote.buyer_id
        for item in extracted_data["line_items"]:
            mapping = await map_charge(item["description"], buyer_id, db)
            
            ic = InvoiceCharge(
                invoice_id=invoice.id,
                raw_charge_name=item["description"],
                rate=item["price"],
                qty=item["quantity"],
                amount=item["total"],
                basis="Per Shipment", # Defaulting basis as requested
                **mapping
            )
            db.add(ic)

        await db.commit()
        await db.refresh(invoice)
        
        return await build_invoice_out(invoice, db, include_charges=True)
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.patch("/charges/{charge_id}/mapping", status_code=status.HTTP_204_NO_CONTENT)
async def update_invoice_charge_mapping(
    charge_id: int,
    body: UpdateChargeMappingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    result = await db.execute(select(InvoiceCharge).where(InvoiceCharge.id == charge_id))
    ic = result.scalar_one_or_none()
    if not ic:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Invoice charge not found"})

    invoice = await db.get(Invoice, ic.invoice_id)
    quote = await db.get(Quote, invoice.quote_id)
    
    if current_user["role"] != "super_admin" and quote.buyer_id != current_user["company_id"]:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only the buyer can correct mappings"})

    charge = await db.get(Charge, body.mapped_charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Mapped charge not found"})

    ic.mapped_charge_id = body.mapped_charge_id
    ic.mapped_charge_name = charge.name
    ic.mapping_tier = "HUMAN"
    ic.low_confidence = False
    ic.similarity_score = 1.0

    # Self-learning: Add alias
    existing = await db.execute(
        select(ChargeAlias).where(
            ChargeAlias.charge_id == body.mapped_charge_id,
            ChargeAlias.alias == ic.raw_charge_name
        )
    )
    if not existing.scalar_one_or_none():
        db.add(ChargeAlias(charge_id=body.mapped_charge_id, alias=ic.raw_charge_name))

    await db.commit()
    return None

@router.post("/{invoice_id}/analyze", response_model=list[dict])
async def analyze_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    invoice = await db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Invoice not found"})

    quote = await db.get(Quote, invoice.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Associated quote not found"})

    if current_user["role"] != "super_admin" and quote.buyer_id != current_user["company_id"]:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    # ── Step 1: Clear old anomalies so re-runs are clean ──────────────────────
    await db.execute(delete(Anomaly).where(Anomaly.invoice_id == invoice_id))
    await db.flush()

    anomalies_to_create = []

    # ── Step 2: Load invoice charges and quote charges ─────────────────────────
    inv_charges_result = await db.execute(
        select(InvoiceCharge).where(InvoiceCharge.invoice_id == invoice_id)
    )
    inv_charges = inv_charges_result.scalars().all()

    from app.models.quote import QuoteCharge
    quote_charges_result = await db.execute(
        select(QuoteCharge).where(QuoteCharge.quote_id == quote.id)
    )
    quote_charges = quote_charges_result.scalars().all()

    # ── Step 3: Build lookup maps keyed by mapped_charge_id ───────────────────
    # For quote: mapped_charge_id → quote_charge
    # Use first match if somehow duplicated
    quote_map: dict[int, QuoteCharge] = {}
    for qc in quote_charges:
        if qc.mapped_charge_id is not None and qc.mapped_charge_id not in quote_map:
            quote_map[qc.mapped_charge_id] = qc

    # Track which quote charge IDs were matched by invoice charges
    matched_quote_charge_ids: set[int] = set()

    # ── Step 4: Walk invoice charges ──────────────────────────────────────────
    for ic in inv_charges:
        # Case A: invoice charge couldn't be mapped at all
        if ic.mapped_charge_id is None:
            anomalies_to_create.append(Anomaly(
                invoice_id=invoice_id,
                invoice_charge_id=ic.id,
                flag_type="UNEXPECTED_CHARGE",
                description=f"'{ic.raw_charge_name}' could not be mapped to any charge in the quote",
                variance=round(float(ic.amount), 2),
            ))
            continue

        # Case B: mapped but not present in quote at all
        if ic.mapped_charge_id not in quote_map:
            anomalies_to_create.append(Anomaly(
                invoice_id=invoice_id,
                invoice_charge_id=ic.id,
                flag_type="UNEXPECTED_CHARGE",
                description=f"'{ic.raw_charge_name}' (mapped to '{ic.mapped_charge_name}') was not in the original quote",
                variance=round(float(ic.amount), 2),
            ))
            continue

        # Case C: found a matching quote charge — compare line by line
        qc = quote_map[ic.mapped_charge_id]
        matched_quote_charge_ids.add(ic.mapped_charge_id)

        inv_amount = round(float(ic.amount), 2)
        quote_amount = round(float(qc.amount), 2)
        inv_rate = round(float(ic.rate), 2)
        quote_rate = round(float(qc.rate), 2)

        if ic.basis != qc.basis:
            anomalies_to_create.append(Anomaly(
                invoice_id=invoice_id,
                invoice_charge_id=ic.id,
                flag_type="BASIS_MISMATCH",
                description=f"'{ic.mapped_charge_name}': basis changed from '{qc.basis}' (quote) to '{ic.basis}' (invoice)",
                variance=None,
            ))

        if inv_rate != quote_rate:
            anomalies_to_create.append(Anomaly(
                invoice_id=invoice_id,
                invoice_charge_id=ic.id,
                flag_type="RATE_MISMATCH",
                description=f"'{ic.mapped_charge_name}': rate changed from {quote_rate} (quote) to {inv_rate} (invoice)",
                variance=round(inv_rate - quote_rate, 2),
            ))

        if inv_amount != quote_amount:
            anomalies_to_create.append(Anomaly(
                invoice_id=invoice_id,
                invoice_charge_id=ic.id,
                flag_type="AMOUNT_MISMATCH",
                description=f"'{ic.mapped_charge_name}': amount changed from {quote_amount} (quote) to {inv_amount} (invoice)",
                variance=round(inv_amount - quote_amount, 2),
            ))

    # ── Step 5: Quote charges missing from invoice ─────────────────────────────
    for qc in quote_charges:
        if qc.mapped_charge_id is None:
            continue  # unmapped quote charge — can't track it
        if qc.mapped_charge_id not in matched_quote_charge_ids:
            anomalies_to_create.append(Anomaly(
                invoice_id=invoice_id,
                invoice_charge_id=None,
                flag_type="MISSING_CHARGE",
                description=f"'{qc.mapped_charge_name or qc.raw_charge_name}' was in the quote but missing from the invoice",
                variance=round(-float(qc.amount), 2),  # negative = undercharged
            ))

    # ── Step 6: Duplicate invoice check ───────────────────────────────────────
    dup_result = await db.execute(
        select(Invoice).where(
            Invoice.quote_id == quote.id,
            Invoice.id != invoice_id
        )
    )
    duplicates = dup_result.scalars().all()
    if duplicates:
        dup_numbers = ", ".join(d.invoice_number for d in duplicates)
        anomalies_to_create.append(Anomaly(
            invoice_id=invoice_id,
            invoice_charge_id=None,
            flag_type="DUPLICATE_INVOICE",
            description=f"Quote {quote.quote_ref} already has invoice(s): {dup_numbers}",
            variance=None,
        ))

    # ── Step 7: E&I Telemetry Forensics ────────────────────────────────────────
    # Read telemetry_data from the parent quote (JSONB, nullable).
    # Guard order:
    #   a) column may be NULL             → skip silently
    #   b) JSONB root may not be a list   → skip with a warning (corrupt data)
    #   c) engine itself may raise        → log + skip; never kill financial results
    raw_telemetry = getattr(quote, "telemetry_data", None)

    if raw_telemetry is not None:
        if not isinstance(raw_telemetry, list):
            # Corrupt / unexpected JSONB shape — log and skip
            logger.warning(
                "analyze_invoice: quote %s telemetry_data is %s, expected list — skipping forensics.",
                quote.id,
                type(raw_telemetry).__name__,
            )
        elif len(raw_telemetry) == 0:
            # Column present but empty array — nothing to analyse
            logger.info(
                "analyze_invoice: quote %s has an empty telemetry_data array — skipping forensics.",
                quote.id,
            )
        else:
            try:
                # Cold-chain SLA threshold: 5 °C (adjust per commodity as needed)
                TEMP_SLA_THRESHOLD_C = 5.0

                telemetry_anomalies = _forensics.analyze(
                    raw_telemetry,
                    temp_threshold_c=TEMP_SLA_THRESHOLD_C,
                )

                for ta in telemetry_anomalies:
                    # Fix: use explicit None check so variance=0.0 is preserved
                    raw_variance = ta.get("variance")
                    if raw_variance is not None:
                        try:
                            db_variance = round(float(raw_variance), 2) or None
                        except (TypeError, ValueError):
                            db_variance = None
                    else:
                        db_variance = None

                    anomalies_to_create.append(Anomaly(
                        invoice_id=invoice_id,
                        invoice_charge_id=None,  # telemetry flags are shipment-level
                        flag_type=ta["flag_type"],
                        description=ta["description"],
                        variance=db_variance,
                    ))

                logger.info(
                    "analyze_invoice: %d telemetry anomaly/ies appended for invoice %s.",
                    len(telemetry_anomalies),
                    invoice_id,
                )

            except Exception as exc:
                # Isolate: log the failure but don't let it wipe financial anomalies
                logger.error(
                    "analyze_invoice: telemetry forensics raised an unexpected error "
                    "for quote %s — skipping. Error: %s",
                    quote.id,
                    exc,
                    exc_info=True,
                )

    # ── Step 8: Persist and return ────────────────────────────────────────────
    for a in anomalies_to_create:
        db.add(a)
    await db.commit()

    # Re-fetch to get IDs
    result = await db.execute(select(Anomaly).where(Anomaly.invoice_id == invoice_id))
    saved = result.scalars().all()

    return [
        {
            "id": a.id,
            "invoice_id": a.invoice_id,
            "invoice_charge_id": a.invoice_charge_id,
            "flag_type": a.flag_type,
            "description": a.description,
            "variance": float(a.variance) if a.variance is not None else None,
        }
        for a in saved
    ]


@router.get("/{invoice_id}/anomalies", response_model=list[dict])
async def get_invoice_anomalies(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    invoice = await db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Invoice not found"})

    quote = await db.get(Quote, invoice.quote_id)
    if current_user["role"] != "super_admin" and quote.buyer_id != current_user["company_id"]:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    result = await db.execute(select(Anomaly).where(Anomaly.invoice_id == invoice_id))
    anomalies = result.scalars().all()
    return [
        {
            "id": a.id,
            "invoice_id": a.invoice_id,
            "invoice_charge_id": a.invoice_charge_id,
            "flag_type": a.flag_type,
            "description": a.description,
            "variance": float(a.variance) if a.variance else None,
        }
        for a in anomalies
    ]
