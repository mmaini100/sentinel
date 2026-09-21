"""EvaluationRun model — tracks fault injection evaluation results."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Boolean, ForeignKey, Text, text
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationRun(injected={self.injected_fault_type!r}, "
            f"predicted={self.predicted_fault_type!r}, matched={self.matched})>"
        )
