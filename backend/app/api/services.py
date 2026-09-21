"""
Services API router.

GET /services — list services with dependency graph
GET /services/{id}/events — paginated events for a service
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.event import Event
from app.models.service import Service
from app.schemas.events import EventListResponse, EventResponse
from app.schemas.services import ServiceListResponse, ServiceResponse, FaultTriggerRequest
from app.config import settings
import redis.asyncio as redis


router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=ServiceListResponse)
async def list_services(
    session: AsyncSession = Depends(get_session),
) -> ServiceListResponse:
    """List all services with their dependency graph."""
    result = await session.execute(
        select(Service).options(selectinload(Service.dependencies))
    )
    services = result.scalars().all()

    return ServiceListResponse(
        services=[ServiceResponse.model_validate(s) for s in services],
        total=len(services),
    )


@router.get("/{service_id}/events", response_model=EventListResponse)
async def list_service_events(
    service_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    anomalous_only: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> EventListResponse:
    """Get paginated events for a specific service."""
    # Verify service exists
    svc_result = await session.execute(
        select(Service).where(Service.id == service_id)
    )
    if not svc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Service not found")

    # Build query
    query = select(Event).where(Event.service_id == service_id)
    count_query = select(func.count()).select_from(Event).where(
        Event.service_id == service_id
    )

    if anomalous_only:
        query = query.where(Event.is_anomalous.is_(True))
        count_query = count_query.where(Event.is_anomalous.is_(True))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    result = await session.execute(
        query.order_by(Event.timestamp.desc()).offset(offset).limit(page_size)
    )
    events = result.scalars().all()

    return EventListResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )

@router.post("/trigger-fault")
async def trigger_fault(
    request: FaultTriggerRequest,
) -> dict[str, str]:
    """Trigger a simulated fault on a service via Redis streams."""
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        # XADD fault_commands:<service_name> * fault_type <fault_type> duration_seconds <duration_seconds>
        stream_key = f"fault_commands:{request.service_name}"
        fields = {
            "fault_type": request.fault_type,
            "duration_seconds": str(request.duration_seconds),
        }
        await redis_client.xadd(stream_key, fields)
        return {"status": "success", "message": f"Fault triggered on {request.service_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await redis_client.aclose()
