"""
Incidents API router.

GET /incidents — paginated, filterable by status/severity
GET /incidents/{id} — full incident detail with events + root cause analyses
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_session
from app.models.event import Event
from app.models.incident import Incident, IncidentEvent
from app.models.root_cause import RootCauseAnalysis
from app.models.service import Service
from app.schemas.events import EventResponse
from app.schemas.incidents import (
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentResponse,
    RootCauseAnalysisResponse,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


async def _get_incident_service_names(
    incident: Incident,
    session: AsyncSession,
) -> list[str]:
    """Get the names of all services implicated in an incident."""
    event_ids = [ie.event_id for ie in incident.incident_events]
    if not event_ids:
        return []

    result = await session.execute(
        select(Service.name)
        .join(Event, Event.service_id == Service.id)
        .where(Event.id.in_(event_ids))
        .distinct()
    )
    return list(result.scalars().all())


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(open|resolved)$"),
    severity: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
    session: AsyncSession = Depends(get_session),
) -> IncidentListResponse:
    """List incidents with pagination and optional filters."""
    query = select(Incident).options(selectinload(Incident.incident_events))
    count_query = select(func.count()).select_from(Incident)

    if status:
        query = query.where(Incident.status == status)
        count_query = count_query.where(Incident.status == status)

    if severity:
        query = query.where(Incident.severity == severity)
        count_query = count_query.where(Incident.severity == severity)

    # Total count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Paginated results
    offset = (page - 1) * page_size
    result = await session.execute(
        query.order_by(Incident.created_at.desc()).offset(offset).limit(page_size)
    )
    incidents = result.scalars().all()

    # Build response with event counts and service names
    incident_responses = []
    for inc in incidents:
        service_names = await _get_incident_service_names(inc, session)
        incident_responses.append(
            IncidentResponse(
                id=inc.id,
                title=inc.title,
                status=inc.status,
                severity=inc.severity,
                created_at=inc.created_at,
                resolved_at=inc.resolved_at,
                event_count=len(inc.incident_events),
                service_names=service_names,
            )
        )

    return IncidentListResponse(
        incidents=incident_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stream")
async def stream_incidents(session: AsyncSession = Depends(get_session)):
    """
    Server-Sent Events endpoint for real-time incident streaming.
    Polls the database for new incidents and yields them as JSON.
    """
    async def event_generator():
        last_checked_id = None
        
        while True:
            # Simple polling: check for the latest incident we haven't sent yet
            query = select(Incident).order_by(Incident.created_at.desc()).limit(1)
            result = await session.execute(query)
            incident = result.scalars().first()
            
            if incident and str(incident.id) != last_checked_id:
                last_checked_id = str(incident.id)
                # We yield the schema representation
                incident_dict = {
                    "id": str(incident.id),
                    "status": incident.status,
                    "severity": incident.severity,
                    "created_at": incident.created_at.isoformat() if incident.created_at else None,
                    "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                }
                import json
                yield {
                    "event": "new_incident",
                    "data": json.dumps(incident_dict)
                }
                
            await asyncio.sleep(2.0)

    return EventSourceResponse(event_generator())


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> IncidentDetailResponse:
    """Get full incident detail including events and root cause analyses."""
    result = await session.execute(
        select(Incident)
        .where(Incident.id == incident_id)
        .options(
            selectinload(Incident.incident_events),
            selectinload(Incident.root_cause_analyses),
        )
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Load the actual events
    event_ids = [ie.event_id for ie in incident.incident_events]
    events = []
    if event_ids:
        events_result = await session.execute(
            select(Event)
            .where(Event.id.in_(event_ids))
            .options(selectinload(Event.service))
            .order_by(Event.timestamp.asc())
        )
        
        for e in events_result.scalars().all():
            resp = EventResponse.model_validate(e)
            if hasattr(e, "service") and e.service:
                resp.service_name = e.service.name
            events.append(resp)

    # Get service names
    service_names = await _get_incident_service_names(incident, session)

    # Build RCA responses
    rcas = [
        RootCauseAnalysisResponse.model_validate(r)
        for r in incident.root_cause_analyses
    ]

    return IncidentDetailResponse(
        id=incident.id,
        title=incident.title,
        status=incident.status,
        severity=incident.severity,
        created_at=incident.created_at,
        resolved_at=incident.resolved_at,
        events=events,
        root_cause_analyses=rcas,
        service_names=service_names,
    )


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> IncidentResponse:
    """Mark an incident as resolved."""
    from datetime import datetime, timezone
    
    result = await session.execute(
        select(Incident)
        .where(Incident.id == incident_id)
        .options(selectinload(Incident.incident_events))
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status == "resolved":
        # Guard against double-resolution
        raise HTTPException(status_code=409, detail="Incident is already resolved")

    incident.status = "resolved"
    incident.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await session.commit()
    await session.refresh(incident)
    
    service_names = await _get_incident_service_names(incident, session)

    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        status=incident.status,
        severity=incident.severity,
        created_at=incident.created_at,
        resolved_at=incident.resolved_at,
        event_count=len(incident.incident_events),
        service_names=service_names,
    )

