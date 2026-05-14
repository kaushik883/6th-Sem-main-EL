from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.quote import Quote
from app.models.invoice import Invoice
from app.models.tracking import TrackingEvent

router = APIRouter()


class DashboardStatsOut(BaseModel):
    open_quotes: int
    anomalies_pending: int
    invoices_this_month: int
    total_accepted: int


@router.get("/stats", response_model=DashboardStatsOut)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    role = current_user["role"]
    company_id = current_user["company_id"]

    # Base queries
    q_quotes = select(func.count()).select_from(Quote)
    q_invoices = select(func.count()).select_from(Invoice).join(Quote)

    if role == "forwarder":
        q_quotes = q_quotes.where(Quote.forwarder_id == company_id)
        q_invoices = q_invoices.where(Quote.forwarder_id == company_id)
    elif role == "client":
        q_quotes = q_quotes.where(Quote.buyer_id == company_id)
        q_invoices = q_invoices.where(Quote.buyer_id == company_id)

    open_quotes = await db.scalar(q_quotes.where(Quote.status == "SUBMITTED"))
    total_accepted = await db.scalar(q_quotes.where(Quote.status == "ACCEPTED"))
    
    # Very basic mock for the others
    invoices_this_month = await db.scalar(q_invoices)
    anomalies_pending = 0

    return DashboardStatsOut(
        open_quotes=open_quotes or 0,
        anomalies_pending=anomalies_pending,
        invoices_this_month=invoices_this_month or 0,
        total_accepted=total_accepted or 0,
    )
