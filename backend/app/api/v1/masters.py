from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.master import Airport, Currency

router = APIRouter()


class AirportOut(BaseModel):
    id: int
    name: str
    iata_code: str
    country_id: int | None
    is_active: bool


class CurrencyOut(BaseModel):
    id: int
    name: str
    short_name: str
    is_active: bool


@router.get("/airports", response_model=list[AirportOut])
async def list_airports(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(Airport).where(Airport.is_active == True).order_by(Airport.name))
    return result.scalars().all()


@router.get("/currencies", response_model=list[CurrencyOut])
async def list_currencies(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(Currency).where(Currency.is_active == True).order_by(Currency.name))
    return result.scalars().all()
