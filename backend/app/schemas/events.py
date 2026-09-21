"""Pydantic schemas for events."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    """Response schema for a single event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    service_name: str | None = None
    event_type: str
    payload: dict
    is_anomalous: bool
    anomaly_score: float | None = None
    timestamp: datetime


class EventListResponse(BaseModel):
    """Paginated response for events."""

    events: list[EventResponse]
    total: int
    page: int
    page_size: int
