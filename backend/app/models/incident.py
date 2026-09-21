"""Incident and IncidentEvent models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text, text
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
