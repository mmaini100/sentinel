"""Pydantic schemas for services."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceDependencyResponse(BaseModel):
    """A dependency relationship between two services."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    depends_on_service_id: uuid.UUID


class ServiceResponse(BaseModel):
    """Response schema for a single service."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = ""
    created_at: datetime
    dependencies: list[ServiceDependencyResponse] = []


class ServiceListResponse(BaseModel):
    """Response schema for list of services with dependency graph."""

    services: list[ServiceResponse]
    total: int


class FaultTriggerRequest(BaseModel):
    """Request to trigger a fault on a service."""
    
    service_name: str
    fault_type: str = "latency_spike"
    duration_seconds: int = 60
