from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PartUsage(Base):
    __tablename__ = "part_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True,
    )

    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id"),
        nullable=True,
    )

    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id"),
        nullable=False,
    )

    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    usage_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CONSUMED",
    )

    recorded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    service_request = relationship("ServiceRequest")
    assignment = relationship("Assignment")
    part = relationship("Part")
    warehouse = relationship("Warehouse")