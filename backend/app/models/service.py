"""Service and ServiceDependency models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text, text
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
