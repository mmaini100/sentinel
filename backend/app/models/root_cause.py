"""RootCauseAnalysis model — stores LLM-generated hypotheses."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Text, text
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
