"""SQLAlchemy declarative base for all models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass
"""EvaluationRun model — tracks fault injection evaluation results."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EvaluationRun(Base):
    """Records whether a synthetic fault injection was correctly diagnosed."""

    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    injected_fault_type: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_fault_type: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationRun(injected={self.injected_fault_type!r}, "
            f"predicted={self.predicted_fault_type!r}, matched={self.matched})>"
        )
"""Event model — stores ingested log and metric events."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Event(Base):
    """A single log or metric event from a microservice."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_timestamp", "timestamp"),
        Index("ix_events_service_id", "service_id"),
        Index("ix_events_is_anomalous", "is_anomalous"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="'log' or 'metric'",
    )
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    is_anomalous: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    anomaly_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    # Relationships
    service: Mapped["Service"] = relationship(back_populates="events")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Event(id={self.id}, service_id={self.service_id}, "
            f"type={self.event_type}, anomalous={self.is_anomalous})>"
        )
"""Incident and IncidentEvent models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Incident(Base):
    """A correlated group of anomalous events across one or more services."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="open",
        server_default=text("'open'"),
        comment="'open' or 'resolved'",
    )
    severity: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="medium",
        comment="'low', 'medium', 'high', or 'critical'",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
    )

    # Relationships
    incident_events: Mapped[list["IncidentEvent"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    root_cause_analyses: Mapped[list["RootCauseAnalysis"]] = relationship(  # noqa: F821
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, title={self.title!r}, status={self.status})>"


class IncidentEvent(Base):
    """Join table linking incidents to their constituent events."""

    __tablename__ = "incident_events"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(back_populates="incident_events")
    event: Mapped["Event"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<IncidentEvent(incident={self.incident_id}, event={self.event_id})>"
"""RootCauseAnalysis model — stores LLM-generated hypotheses."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RootCauseAnalysis(Base):
    """An LLM-generated root-cause hypothesis for an incident."""

    __tablename__ = "root_cause_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    cited_event_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="JSON array of event UUIDs cited as evidence",
    )
    llm_provider_used: Mapped[str] = mapped_column(Text, nullable=False)
    raw_llm_response: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
    )
    validation_failed: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="True if citation validation failed after retry",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(  # noqa: F821
        back_populates="root_cause_analyses",
    )

    def __repr__(self) -> str:
        return (
            f"<RootCauseAnalysis(id={self.id}, incident={self.incident_id}, "
            f"confidence={self.confidence})>"
        )
"""Service and ServiceDependency models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Service(Base):
    """Represents a microservice in the monitored topology."""

    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    # Relationships
    events: Mapped[list["Event"]] = relationship(back_populates="service")  # noqa: F821
    dependencies: Mapped[list["ServiceDependency"]] = relationship(
        foreign_keys="ServiceDependency.service_id",
        back_populates="service",
    )
    dependents: Mapped[list["ServiceDependency"]] = relationship(
        foreign_keys="ServiceDependency.depends_on_service_id",
        back_populates="depends_on_service",
    )

    def __repr__(self) -> str:
        return f"<Service(name={self.name!r})>"


class ServiceDependency(Base):
    """Directed dependency edge: service_id depends on depends_on_service_id."""

    __tablename__ = "service_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )
    depends_on_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        foreign_keys=[service_id],
        back_populates="dependencies",
    )
    depends_on_service: Mapped["Service"] = relationship(
        foreign_keys=[depends_on_service_id],
        back_populates="dependents",
    )

    def __repr__(self) -> str:
        return f"<ServiceDependency({self.service_id} -> {self.depends_on_service_id})>"
"""User model — JWT authentication and RBAC."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    """A user account with role-based access control."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="viewer",
        server_default=text("'viewer'"),
        comment="'viewer', 'operator', or 'admin'",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return f"<User(email={self.email!r}, role={self.role})>"
"""
Models package — imports all models so Alembic can discover them.
"""

from app.models.base import Base
from app.models.event import Event
from app.models.evaluation import EvaluationRun
from app.models.incident import Incident, IncidentEvent
from app.models.root_cause import RootCauseAnalysis
from app.models.service import Service, ServiceDependency
from app.models.user import User

__all__ = [
    "Base",
    "Event",
    "EvaluationRun",
    "Incident",
    "IncidentEvent",
    "RootCauseAnalysis",
    "Service",
    "ServiceDependency",
    "User",
]
