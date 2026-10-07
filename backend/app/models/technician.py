from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    technician_skills: Mapped[list["TechnicianSkill"]] = relationship(
        back_populates="skill"
    )


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    employee_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    home_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    workload_score: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    performance_score: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship()
    technician_skills: Mapped[list["TechnicianSkill"]] = relationship(
        back_populates="technician"
    )
    availability: Mapped[list["TechnicianAvailability"]] = relationship(
        back_populates="technician"
    )


class TechnicianSkill(Base):
    __tablename__ = "technician_skills"

    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technicians.id"),
        primary_key=True,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id"),
        primary_key=True,
    )

    proficiency_level: Mapped[str] = mapped_column(
        String(30),
        default="INTERMEDIATE",
        nullable=False,
    )

    technician: Mapped["Technician"] = relationship(
        back_populates="technician_skills"
    )

    skill: Mapped["Skill"] = relationship(
        back_populates="technician_skills"
    )


class TechnicianAvailability(Base):
    __tablename__ = "technician_availability"

    id: Mapped[int] = mapped_column(primary_key=True)

    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technicians.id"),
        nullable=False,
        index=True,
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
        default="AVAILABLE",
        nullable=False,
    )

    technician: Mapped["Technician"] = relationship(
        back_populates="availability"
    )