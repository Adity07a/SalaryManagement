"""Salary request and response schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class InitialSalaryCreate(BaseModel):
    """Initial annual gross salary during employee creation."""

    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    effective_from: date

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.strip().upper()

        if not currency.isalpha():
            raise ValueError("Currency must be a valid ISO-4217 code.")

        return currency


class SalaryCreate(InitialSalaryCreate):
    """Request to add an employee salary record."""


class SalaryResponse(BaseModel):
    """Salary history record with USD equivalent."""

    id: int
    employee_id: int
    amount: Decimal
    currency: str
    effective_from: date
    amount_usd: Decimal
    created_at: datetime
