"""Event model — stores ingested log and metric events."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Boolean, Float, ForeignKey, Index, Text, text
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
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
