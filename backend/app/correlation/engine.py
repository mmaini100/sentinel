"""
Correlation engine — groups anomalous events into incidents.

Uses the service dependency graph to determine which services are related.
When multiple anomalous events occur within a configurable time window
across services connected in the dependency graph, they are grouped into
a single incident rather than creating separate incidents.

Severity is assigned based on:
  - Number of implicated services
  - Peak anomaly score across all events in the incident
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.event import Event
from app.models.incident import Incident, IncidentEvent

logger = logging.getLogger("sentinel.correlation")


class CorrelationEngine:
    """
    Correlates anomalous events into incidents using the dependency graph.

    On each call to `process_anomalous_event`, the engine:
    1. Finds recent anomalous events within the correlation window
    2. Checks if any of those events belong to services connected in the
       dependency graph to the new event's service
    3. If connected events exist, adds the new event to an existing open
       incident (or creates one grouping them all)
    4. If no connected events exist, creates a new single-service incident
    5. Computes and updates severity based on scope and anomaly scores
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._dep_graph: dict[str, set[str]] | None = None

    async def _load_dependency_graph(self) -> dict[str, set[str]]:
        """
        Load the service dependency graph from Redis cache.
        Returns an undirected adjacency map: {service_name: {connected_services}}.
        """
        if self._dep_graph is not None:
            return self._dep_graph

        graph: dict[str, set[str]] = {}
        raw = await self._redis.hgetall("dependency_graph")

        for service_name, deps_json in raw.items():
            deps = json.loads(deps_json)
            if service_name not in graph:
                graph[service_name] = set()
            for dep in deps:
                graph[service_name].add(dep)
                # Make it bidirectional — if A depends on B,
                # a fault in B should also correlate with events in A
                if dep not in graph:
                    graph[dep] = set()
                graph[dep].add(service_name)

        self._dep_graph = graph
        logger.info(f"Loaded dependency graph: { {k: list(v) for k, v in graph.items()} }")
        return graph

    def _get_connected_services(self, service_name: str) -> set[str]:
        """
        Get all services connected (directly or transitively) to the given service.
        Uses BFS to find the full connected component in the dependency graph.
        """
        if not self._dep_graph:
            return {service_name}

        visited = set()
        queue = [service_name]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for neighbor in self._dep_graph.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)

        return visited

    @staticmethod
    def _compute_severity(
        service_count: int,
        peak_anomaly_score: float,
    ) -> str:
        """
        Compute incident severity from the number of affected services
        and the peak anomaly score.

        Rules:
          - critical: 3+ services OR peak score > 5.0
          - high: 2+ services OR peak score > 4.0
          - medium: peak score > 3.0
          - low: everything else
        """
        if service_count >= 3 or peak_anomaly_score > 5.0:
            return "critical"
        elif service_count >= 2 or peak_anomaly_score > 4.0:
            return "high"
        elif peak_anomaly_score > 3.0:
            return "medium"
        else:
            return "low"

    async def process_anomalous_event(
        self,
        event: Event,
        service_name: str,
        session: AsyncSession,
    ) -> Incident | None:
        """
        Process a newly detected anomalous event:
        1. Look for recent anomalous events in connected services
        2. Either add to an existing open incident or create a new one
        3. Update severity

        Returns the Incident if one was created or updated, None on error.
        """
        try:
            graph = await self._load_dependency_graph()
            connected_services = self._get_connected_services(service_name)

            window_start = datetime.now(timezone.utc) - timedelta(
                seconds=settings.CORRELATION_WINDOW_SECONDS
            )

            # Find open incidents that contain events from connected services
            # within the time window
            from sqlalchemy.orm import selectinload

            open_incidents_result = await session.execute(
                select(Incident)
                .where(Incident.status == "open")
                .where(Incident.created_at >= window_start)
                .options(selectinload(Incident.incident_events))
            )
            open_incidents = open_incidents_result.scalars().all()

            # Check if any open incident already has events from connected services
            target_incident: Incident | None = None

            for incident in open_incidents:
                # Get service IDs for events in this incident
                for ie in incident.incident_events:
                    event_result = await session.execute(
                        select(Event).where(Event.id == ie.event_id)
                    )
                    existing_event = event_result.scalar_one_or_none()
                    if existing_event:
                        # Look up service name from cache
                        existing_svc_result = await session.execute(
                            select(Event.service_id).where(Event.id == ie.event_id)
                        )
                        existing_svc_id = existing_svc_result.scalar_one_or_none()
                        if existing_svc_id:
                            # Check if this service is in our connected set
                            from app.models.service import Service
                            svc_result = await session.execute(
                                select(Service.name).where(Service.id == existing_svc_id)
                            )
                            svc_name = svc_result.scalar_one_or_none()
                            if svc_name and svc_name in connected_services:
                                target_incident = incident
                                break

                if target_incident:
                    break

            if target_incident:
                # Add event to existing incident
                ie = IncidentEvent(
                    incident_id=target_incident.id,
                    event_id=event.id,
                )
                session.add(ie)

                # Recalculate severity
                all_event_ids = [ie.event_id for ie in target_incident.incident_events]
                all_event_ids.append(event.id)

                events_result = await session.execute(
                    select(Event).where(Event.id.in_(all_event_ids))
                )
                all_events = events_result.scalars().all()

                service_ids = {e.service_id for e in all_events}
                peak_score = max(
                    (e.anomaly_score or 0.0 for e in all_events), default=0.0
                )

                target_incident.severity = self._compute_severity(
                    len(service_ids), peak_score
                )

                await session.commit()
                logger.info(
                    f"Added event {event.id} to existing incident "
                    f"{target_incident.id} (severity={target_incident.severity})"
                )
                return target_incident

            else:
                # Create new incident
                peak_score = event.anomaly_score or 0.0
                severity = self._compute_severity(1, peak_score)

                incident = Incident(
                    id=uuid.uuid4(),
                    title=f"Anomaly detected in {service_name}",
                    status="open",
                    severity=severity,
                )
                session.add(incident)
                await session.flush()

                ie = IncidentEvent(
                    incident_id=incident.id,
                    event_id=event.id,
                )
                session.add(ie)
                await session.commit()

                logger.info(
                    f"Created new incident {incident.id}: "
                    f"'{incident.title}' (severity={severity})"
                )
                return incident

        except Exception:
            logger.exception("Error in correlation engine")
            await session.rollback()
            return None
