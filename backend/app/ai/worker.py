"""
Background worker that watches for 'stable' incidents and triggers RCA.
An incident is considered 'stable' if it hasn't received new events in >30s,
and doesn't already have an RCA.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.llm import generate_root_cause_analysis
from app.config import settings
from app.database import async_session_factory
from app.models.event import Event
from app.models.incident import Incident
from app.models.root_cause import RootCauseAnalysis
from app.models.service import Service

logger = logging.getLogger("sentinel.ai.worker")


class RCAWorker:
    """Polls for stable incidents and triggers AI Root Cause Analysis."""

    def __init__(self) -> None:
        self._running = False
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def _get_stable_incidents(self, session: AsyncSession) -> list[Incident]:
        """Find incidents older than 15s that lack an RCA."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=15)

        # We query for incidents that don't have an RCA
        # We'll check the 'latest event timestamp' in python to be safe.
        query = (
            select(Incident)
            .where(Incident.status == "open")
            .where(Incident.created_at < cutoff)
            .outerjoin(RootCauseAnalysis)
            .where(RootCauseAnalysis.id.is_(None))
            .options(selectinload(Incident.incident_events))
        )
        
        result = await session.execute(query)
        incidents = result.scalars().all()
        
        stable_incidents = []
        for incident in incidents:
            # Get latest event for this incident
            event_ids = [ie.event_id for ie in incident.incident_events]
            if not event_ids:
                continue
                
            latest_event_result = await session.execute(
                select(Event.timestamp)
                .where(Event.id.in_(event_ids))
                .order_by(Event.timestamp.desc())
                .limit(1)
            )
            latest_ts = latest_event_result.scalar_one_or_none()
            
            if latest_ts and latest_ts < cutoff:
                stable_incidents.append(incident)
                
        return stable_incidents

    async def _build_incident_context(
        self, incident: Incident, session: AsyncSession
    ) -> tuple[list[dict], dict[str, list[str]]]:
        """Gather all events and the relevant dependency graph context."""
        event_ids = [ie.event_id for ie in incident.incident_events]
        events_result = await session.execute(
            select(Event, Service.name)
            .join(Service, Event.service_id == Service.id)
            .where(Event.id.in_(event_ids))
            .order_by(Event.timestamp.asc())
        )
        
        events_data = []
        services_involved = set()
        
        for event, service_name in events_result.all():
            services_involved.add(service_name)
            events_data.append({
                "id": str(event.id),
                "service": service_name,
                "type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "is_anomalous": event.is_anomalous,
                "score": event.anomaly_score,
                "payload": event.payload,
            })
            
        # Get graph context
        r = await self._get_redis()
        graph_context = {}
        for svc in services_involved:
            deps_json = await r.hget("dependency_graph", svc)
            if deps_json:
                import json
                graph_context[svc] = json.loads(deps_json)
                
        return events_data, graph_context

    async def run(self) -> None:
        """Main poll loop."""
        self._running = True
        logger.info("Starting AI RCA worker...")

        while self._running:
            try:
                async with async_session_factory() as session:
                    incidents = await self._get_stable_incidents(session)
                    
                    for incident in incidents:
                        logger.info(f"Processing RCA for stable incident {incident.id}")
                        events_data, graph_context = await self._build_incident_context(incident, session)
                        
                        await generate_root_cause_analysis(
                            incident=incident,
                            events_data=events_data,
                            dependency_graph=graph_context,
                            session=session,
                        )
                        
            except Exception:
                logger.exception("Error in RCA worker loop")
                
            # Sleep until next poll
            await asyncio.sleep(5)

    async def stop(self) -> None:
        self._running = False
        if self._redis:
            await self._redis.aclose()
        logger.info("AI RCA worker stopped")
