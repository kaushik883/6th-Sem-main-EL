from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
import uuid
import os
import datetime

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
    if current_user["role"] != "super_admin" and quote.buyer_id != current_user["company_id"]:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    # Stub
    await db.execute(delete(Anomaly).where(Anomaly.invoice_id == invoice_id))
    await db.commit()
    return []


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
