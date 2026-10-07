from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    maintenance_mode: Mapped[str | None] = mapped_column(String(50))
    machine_type: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_templates.id"),
        nullable=False,
    )
    item_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class WorkChecklist(Base):
    __tablename__ = "work_checklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"),
        nullable=False,
    )
    checklist_item_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_items.id"),
        nullable=False,
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    notes: Mapped[str | None] = mapped_column(Text)