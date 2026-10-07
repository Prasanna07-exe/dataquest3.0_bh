from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ServiceHistory(Base):
    __tablename__ = "service_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
        index=True,
    )

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    request_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    maintenance_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    issue_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    failure_mode: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    resolution_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    technician_id: Mapped[int | None] = mapped_column(
        ForeignKey("technicians.id"),
        nullable=True,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    machine: Mapped["Machine"] = relationship()
    service_request: Mapped["ServiceRequest"] = relationship()
    technician: Mapped["Technician | None"] = relationship()