from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    request_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id"),
        nullable=False,
        index=True,
    )

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    maintenance_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="MEDIUM",
    )

    state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DRAFT",
        index=True,
    )

    requested_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    requested_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    customer: Mapped["Customer"] = relationship()
    site: Mapped["Site"] = relationship()
    machine: Mapped["Machine"] = relationship()
    creator: Mapped["User"] = relationship()

class RequestAIAnalysis(Base):
    __tablename__ = "request_ai_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)

    request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    issue_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_mode: Mapped[str | None] = mapped_column(String(150), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(30), nullable=True)

    required_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    required_tools: Mapped[list | None] = mapped_column(JSON, nullable=True)
    required_parts: Mapped[list | None] = mapped_column(JSON, nullable=True)
    similar_failures: Mapped[list | None] = mapped_column(JSON, nullable=True)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    analysis_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    request: Mapped["ServiceRequest"] = relationship()