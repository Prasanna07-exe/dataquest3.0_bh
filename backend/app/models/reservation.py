from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResourceReservation(Base):
    __tablename__ = "resource_reservations"

    id: Mapped[int] = mapped_column(primary_key=True)

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id"),
        nullable=True,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    resource_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="RESERVED",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    service_request: Mapped["ServiceRequest"] = relationship()
    assignment: Mapped["Assignment | None"] = relationship()