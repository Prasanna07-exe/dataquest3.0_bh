from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WorkLog(Base):
    __tablename__ = "work_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technicians.id"),
        nullable=False,
        index=True,
    )

    log_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    service_request: Mapped["ServiceRequest"] = relationship()
    technician: Mapped["Technician"] = relationship()