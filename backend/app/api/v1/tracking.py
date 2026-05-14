from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.tracking import TrackingEvent
from app.models.quote import Quote
from app.models.company import Company
from app.models.master import Airport

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_tracking(
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

    result = await db.execute(q)
    quotes = result.scalars().all()

    tracking_list = []
    for qt in quotes:
        # Get latest event
        ev_result = await db.execute(
            select(TrackingEvent).where(TrackingEvent.quote_id == qt.id).order_by(TrackingEvent.event_time.desc()).limit(1)
        )
        latest_event = ev_result.scalar_one_or_none()

        fwd = await db.get(Company, qt.forwarder_id)
        buyer = await db.get(Company, qt.buyer_id)
        origin = await db.get(Airport, qt.origin_airport_id)
        dest = await db.get(Airport, qt.destination_airport_id)

        tracking_list.append({
            "quote_id": qt.id,
            "quote_ref": qt.quote_ref,
            "tracking_number": qt.tracking_number,
            "origin": origin.iata_code if origin else "",
            "destination": dest.iata_code if dest else "",
            "current_status": latest_event.status if latest_event else "Pending",
            "last_event_time": latest_event.event_time.isoformat() if latest_event else None,
            "forwarder_name": fwd.name if fwd else "",
            "buyer_name": buyer.name if buyer else ""
        })

    return tracking_list


@router.get("/{quote_id}/events", response_model=list[dict])
async def get_tracking_events(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(TrackingEvent).where(TrackingEvent.quote_id == quote_id).order_by(TrackingEvent.event_time.desc())
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "quote_id": e.quote_id,
            "event_time": e.event_time.isoformat(),
            "location": e.location,
            "status": e.status,
            "description": e.description
        }
        for e in events
    ]
