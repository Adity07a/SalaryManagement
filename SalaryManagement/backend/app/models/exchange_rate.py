from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.salary import Salary


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="currency_iso4217_format",
        ),
        CheckConstraint("rate_to_base > 0", name="rate_to_base_positive"),
    )

    currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    rate_to_base: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)

    salaries: Mapped[list[Salary]] = relationship(
        "Salary",
        back_populates="exchange_rate",
        passive_deletes=True,
    )
