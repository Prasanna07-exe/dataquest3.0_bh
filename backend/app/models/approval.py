from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    approved_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    service_request: Mapped["ServiceRequest"] = relationship()
    approver: Mapped["User"] = relationship()