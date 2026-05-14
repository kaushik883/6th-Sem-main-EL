from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.master import Charge, ChargeAlias

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class AliasOut(BaseModel):
    id: int
    charge_id: int
    alias: str


class ChargeOut(BaseModel):
    id: int
    company_id: int
    name: str
    short_name: str
    is_active: bool
    aliases: list[AliasOut] = []


class CreateChargeRequest(BaseModel):
    name: str
    short_name: str


class UpdateChargeRequest(BaseModel):
    name: str | None = None
    short_name: str | None = None
    is_active: bool | None = None


class CreateAliasRequest(BaseModel):
    alias: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ChargeOut])
async def list_charges(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] == "forwarder":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Forwarders cannot access charge master"})

    company_id = current_user["company_id"]
    result = await db.execute(
        select(Charge)
        .where(Charge.company_id == company_id)
        .options(selectinload(Charge.aliases))
        .order_by(Charge.name)
    )
    return result.scalars().all()


@router.post("", response_model=ChargeOut, status_code=status.HTTP_201_CREATED)
async def create_charge(
    body: CreateChargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    if not current_user.get("is_admin") and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only client admins can create charges"})
        
    company_id = current_user["company_id"]
    
    # Length validation
    if len(body.name) < 3 or len(body.name) > 255:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Charge name must be 3-255 characters"})
    if len(body.short_name) < 2 or len(body.short_name) > 50:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Short name must be 2-50 characters"})

    # Uniqueness check
    existing = await db.execute(select(Charge).where(Charge.company_id == company_id, Charge.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Charge name already exists in this company"})
        
    existing_short = await db.execute(select(Charge).where(Charge.company_id == company_id, Charge.short_name == body.short_name))
    if existing_short.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Short name already exists in this company"})

    charge = Charge(
        company_id=company_id,
        name=body.name,
        short_name=body.short_name,
        is_active=True,
    )
    db.add(charge)
    await db.commit()

    result = await db.execute(
        select(Charge).where(Charge.id == charge.id).options(selectinload(Charge.aliases))
    )
    return result.scalar_one()


@router.patch("/{charge_id}", response_model=ChargeOut)
async def update_charge(
    charge_id: int,
    body: UpdateChargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    if not current_user.get("is_admin") and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only client admins can edit charges"})

    result = await db.execute(
        select(Charge)
        .where(Charge.id == charge_id, Charge.company_id == current_user["company_id"])
        .options(selectinload(Charge.aliases))
    )
    charge = result.scalar_one_or_none()
    if not charge:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Charge not found"})

    if body.name is not None:
        if len(body.name) < 3 or len(body.name) > 255:
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Charge name must be 3-255 characters"})
        existing = await db.execute(select(Charge).where(Charge.company_id == charge.company_id, Charge.name == body.name, Charge.id != charge_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Charge name already exists"})
        charge.name = body.name

    if body.short_name is not None:
        if len(body.short_name) < 2 or len(body.short_name) > 50:
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Short name must be 2-50 characters"})
        existing = await db.execute(select(Charge).where(Charge.company_id == charge.company_id, Charge.short_name == body.short_name, Charge.id != charge_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Short name already exists"})
        charge.short_name = body.short_name

    if body.is_active is not None:
        charge.is_active = body.is_active

    await db.commit()
    await db.refresh(charge)
    return charge


@router.post("/{charge_id}/aliases", response_model=AliasOut, status_code=status.HTTP_201_CREATED)
async def add_alias(
    charge_id: int,
    body: CreateAliasRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    if not current_user.get("is_admin") and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only client admins can add aliases"})

    if len(body.alias) < 1 or len(body.alias) > 255:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Alias must be 1-255 characters"})

    # Verify charge belongs to company
    result = await db.execute(
        select(Charge).where(Charge.id == charge_id, Charge.company_id == current_user["company_id"])
    )
    charge = result.scalar_one_or_none()
    if not charge:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Charge not found"})

    # Verify uniqueness
    existing = await db.execute(select(ChargeAlias).where(ChargeAlias.charge_id == charge_id, ChargeAlias.alias == body.alias))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Alias already exists for this charge"})

    alias = ChargeAlias(charge_id=charge_id, alias=body.alias)
    db.add(alias)
    await db.commit()
    await db.refresh(alias)
    return alias


@router.delete("/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alias(
    alias_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("client", "super_admin")),
):
    if not current_user.get("is_admin") and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only client admins can delete aliases"})

    result = await db.execute(
        select(ChargeAlias, Charge)
        .join(Charge, ChargeAlias.charge_id == Charge.id)
        .where(ChargeAlias.id == alias_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Alias not found"})
        
    alias, charge = row
    if charge.company_id != current_user["company_id"] and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Alias not found"})

    await db.delete(alias)
    await db.commit()
    return None
