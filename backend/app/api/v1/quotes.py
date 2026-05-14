import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.quote import Quote, QuoteCharge
from app.models.master import Charge, ChargeAlias
from app.models.company import Company
from app.models.master import Airport, Currency

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class QuoteChargeIn(BaseModel):
    raw_charge_name: str
    rate: float
    basis: str
    qty: float
    amount: float


class CreateQuoteRequest(BaseModel):
    buyer_id: int
    origin_airport_id: int
    destination_airport_id: int
    tracking_number: str
    gross_weight: float
    volumetric_weight: float
    chargeable_weight: float
    currency_id: int
    charges: list[QuoteChargeIn]


class UpdateQuoteStatusRequest(BaseModel):
    status: str   # "ACCEPTED" | "REJECTED"
    rejection_note: str | None = None


class UpdateChargeMappingRequest(BaseModel):
    mapped_charge_id: int


class QuoteChargeOut(BaseModel):
    id: int
    raw_charge_name: str
    mapped_charge_id: int | None
    mapped_charge_name: str | None
    similarity_score: float | None
    mapping_tier: str | None
    low_confidence: bool
    rate: float
    basis: str
    qty: float
    amount: float


class QuoteOut(BaseModel):
    id: int
    quote_ref: str
    status: str
    rejection_note: str | None
    created_at: str
    forwarder: dict
    buyer: dict
    origin_airport: dict
    destination_airport: dict
    tracking_number: str
    gross_weight: float
    volumetric_weight: float
    chargeable_weight: float
    currency: dict
    charges: list[QuoteChargeOut] | None = None


# ── Helpers ────────────────────────────────────────────────────────────────────

async def build_quote_out(quote: Quote, db: AsyncSession, include_charges: bool = False) -> dict:
    # Load related data
    fwd = await db.get(Company, quote.forwarder_id)
    buyer = await db.get(Company, quote.buyer_id)
    origin = await db.get(Airport, quote.origin_airport_id)
    dest = await db.get(Airport, quote.destination_airport_id)
    currency = await db.get(Currency, quote.currency_id)

    result = {
        "id": quote.id,
        "quote_ref": quote.quote_ref,
        "status": quote.status,
        "rejection_note": quote.rejection_note,
        "created_at": quote.created_at.isoformat() if quote.created_at else None,
        "forwarder": {"id": fwd.id, "name": fwd.name} if fwd else {},
        "buyer": {"id": buyer.id, "name": buyer.name} if buyer else {},
        "origin_airport": {"iata_code": origin.iata_code, "name": origin.name} if origin else {},
        "destination_airport": {"iata_code": dest.iata_code, "name": dest.name} if dest else {},
        "tracking_number": quote.tracking_number,
        "gross_weight": float(quote.gross_weight),
        "volumetric_weight": float(quote.volumetric_weight),
        "chargeable_weight": float(quote.chargeable_weight),
        "currency": {"short_name": currency.short_name} if currency else {},
    }

    if include_charges:
        charges_result = await db.execute(
            select(QuoteCharge).where(QuoteCharge.quote_id == quote.id)
        )
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


async def map_charge(raw_name: str, buyer_id: int, db: AsyncSession) -> dict:
    """Attempt dictionary match against buyer's charge master (name + aliases)."""
    raw_lower = raw_name.strip().lower()

    # 1. Exact match on charge name
    result = await db.execute(
        select(Charge).where(
            Charge.company_id == buyer_id,
            Charge.is_active == True,
            text("LOWER(name) = :n")
        ).params(n=raw_lower)
    )
    charge = result.scalar_one_or_none()
    if charge:
        return {"mapped_charge_id": charge.id, "mapped_charge_name": charge.name,
                "mapping_tier": "DICTIONARY", "similarity_score": 1.0, "low_confidence": False}

    # 2. Exact match on short_name
    result = await db.execute(
        select(Charge).where(
            Charge.company_id == buyer_id,
            Charge.is_active == True,
            text("LOWER(short_name) = :n")
        ).params(n=raw_lower)
    )
    charge = result.scalar_one_or_none()
    if charge:
        return {"mapped_charge_id": charge.id, "mapped_charge_name": charge.name,
                "mapping_tier": "DICTIONARY", "similarity_score": 1.0, "low_confidence": False}

    # 3. Exact match on aliases
    result = await db.execute(
        select(ChargeAlias, Charge)
        .join(Charge, ChargeAlias.charge_id == Charge.id)
        .where(
            Charge.company_id == buyer_id,
            Charge.is_active == True,
            text("LOWER(charge_aliases.alias) = :n")
        ).params(n=raw_lower)
    )
    row = result.first()
    if row:
        alias, charge = row
        return {"mapped_charge_id": charge.id, "mapped_charge_name": charge.name,
                "mapping_tier": "DICTIONARY", "similarity_score": 0.95, "low_confidence": False}

    # 4. Partial / fuzzy match (contains)
    result = await db.execute(
        select(Charge).where(
            Charge.company_id == buyer_id,
            Charge.is_active == True,
            text("LOWER(name) LIKE :n")
        ).params(n=f"%{raw_lower}%")
    )
    charge = result.scalars().first()
    if charge:
        return {"mapped_charge_id": charge.id, "mapped_charge_name": charge.name,
                "mapping_tier": "DICTIONARY", "similarity_score": 0.75, "low_confidence": True}

    return {"mapped_charge_id": None, "mapped_charge_name": None,
            "mapping_tier": "UNMAPPED", "similarity_score": None, "low_confidence": True}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[dict])
async def list_quotes(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user["role"]
    company_id = current_user["company_id"]

    q = select(Quote)
    if role == "forwarder":
        q = q.where(Quote.forwarder_id == company_id)
    elif role == "client":
        q = q.where(Quote.buyer_id == company_id)
    # super_admin sees all

    q = q.order_by(Quote.created_at.desc())
    result = await db.execute(q)
    quotes = result.scalars().all()

    return [await build_quote_out(qt, db, include_charges=False) for qt in quotes]


@router.get("/{quote_id}", response_model=dict)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Quote not found"})

    role = current_user["role"]
    company_id = current_user["company_id"]
    if role == "forwarder" and quote.forwarder_id != company_id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})
    if role == "client" and quote.buyer_id != company_id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    return await build_quote_out(quote, db, include_charges=True)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_quote(
    body: CreateQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("forwarder", "super_admin")),
):
    forwarder_id = current_user["company_id"]
    quote_ref = f"QR-{int(time.time())}"

    quote = Quote(
        quote_ref=quote_ref,
        status="SUBMITTED",
        forwarder_id=forwarder_id,
        buyer_id=body.buyer_id,
        origin_airport_id=body.origin_airport_id,
        destination_airport_id=body.destination_airport_id,
        tracking_number=body.tracking_number,
        gross_weight=body.gross_weight,
        volumetric_weight=body.volumetric_weight,
        chargeable_weight=max(body.gross_weight, body.volumetric_weight),
        currency_id=body.currency_id,
    )
    db.add(quote)
    await db.flush()  # get quote.id

    for charge_in in body.charges:
        mapping = await map_charge(charge_in.raw_charge_name, body.buyer_id, db)
        qc = QuoteCharge(
            quote_id=quote.id,
            raw_charge_name=charge_in.raw_charge_name,
            rate=charge_in.rate,
            basis=charge_in.basis,
            qty=charge_in.qty,
            amount=charge_in.amount,
            **mapping,
        )
        db.add(qc)

    await db.commit()
    await db.refresh(quote)
    return await build_quote_out(quote, db, include_charges=True)


@router.patch("/{quote_id}/status", response_model=dict)
async def update_quote_status(
    quote_id: int,
    body: UpdateQuoteStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    if body.status not in ("ACCEPTED", "REJECTED"):
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "status must be ACCEPTED or REJECTED"})

    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Quote not found"})

    if current_user["role"] == "client" and quote.buyer_id != current_user["company_id"]:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    quote.status = body.status
    if body.rejection_note:
        quote.rejection_note = body.rejection_note
    await db.commit()
    await db.refresh(quote)
    return await build_quote_out(quote, db, include_charges=True)


@router.patch("/charges/{charge_id}/mapping", status_code=status.HTTP_204_NO_CONTENT)
async def update_quote_charge_mapping(
    charge_id: int,
    body: UpdateChargeMappingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    result = await db.execute(select(QuoteCharge).where(QuoteCharge.id == charge_id))
    qc = result.scalar_one_or_none()
    if not qc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Charge not found"})

    # Get the canonical charge name
    charge = await db.get(Charge, body.mapped_charge_id)
    if not charge:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Mapped charge not found"})

    qc.mapped_charge_id = body.mapped_charge_id
    qc.mapped_charge_name = charge.name
    qc.mapping_tier = "HUMAN"
    qc.low_confidence = False
    qc.similarity_score = 1.0

    # Add raw_charge_name as alias to the charge master for future auto-mapping
    existing = await db.execute(
        select(ChargeAlias).where(
            ChargeAlias.charge_id == body.mapped_charge_id,
            ChargeAlias.alias == qc.raw_charge_name
        )
    )
    if not existing.scalar_one_or_none():
        db.add(ChargeAlias(charge_id=body.mapped_charge_id, alias=qc.raw_charge_name))

    await db.commit()
    return None
