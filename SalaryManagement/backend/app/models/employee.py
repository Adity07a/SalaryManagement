from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.salary import Salary


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("length(country) = 2", name="country_iso2_length"),
        CheckConstraint("country = upper(country)", name="country_uppercase"),
        Index("ix_employees_country", "country"),
        Index("ix_employees_department", "department"),
        Index("ix_employees_job_title", "job_title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    salaries: Mapped[list[Salary]] = relationship(
        "Salary",
        back_populates="employee",
        cascade="all, delete",
        passive_deletes=True,
    )
