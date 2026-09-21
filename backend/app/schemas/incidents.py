"""Pydantic schemas for incidents and root cause analyses."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.events import EventResponse


class RootCauseAnalysisResponse(BaseModel):
    """Response schema for a root cause analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    hypothesis: str
    confidence: float
    cited_event_ids: list
    llm_provider_used: str
    raw_llm_response: dict | None = None
    validation_failed: bool = False
    created_at: datetime
    
    # These fields are extracted from raw_llm_response since they aren't explicitly in the DB model
    status: str = "success"
    recommended_action: str | None = None

    @model_validator(mode='before')
    @classmethod
    def extract_from_raw_response(cls, data: Any):
        # data can be a dict or an ORM object
        raw_resp = getattr(data, 'raw_llm_response', None)
        if isinstance(data, dict):
            raw_resp = data.get('raw_llm_response')
            
        if raw_resp and isinstance(raw_resp, dict):
            if isinstance(data, dict):
                data['status'] = raw_resp.get('status', 'success')
                data['recommended_action'] = raw_resp.get('recommended_action')
            else:
                # If it's an ORM object, Pydantic will read from dict if we return one, or we can just 
                # extract properties into a new dict for validation.
                pass
        return data

    @model_validator(mode='after')
    def set_fields_after(self) -> 'RootCauseAnalysisResponse':
        if self.raw_llm_response:
            self.status = self.raw_llm_response.get('status', 'success')
            self.recommended_action = self.raw_llm_response.get('recommended_action')
        return self


class IncidentResponse(BaseModel):
    """Response schema for an incident (list view)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: str
    severity: str
    created_at: datetime
    resolved_at: datetime | None = None
    event_count: int = 0
    service_names: list[str] = []


class IncidentDetailResponse(BaseModel):
    """Response schema for a single incident with full details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: str
    severity: str
    created_at: datetime
    resolved_at: datetime | None = None
    events: list[EventResponse] = []
    root_cause_analyses: list[RootCauseAnalysisResponse] = []
    service_names: list[str] = []


class IncidentListResponse(BaseModel):
    """Paginated response for incidents."""

    incidents: list[IncidentResponse]
    total: int
    page: int
    page_size: int
