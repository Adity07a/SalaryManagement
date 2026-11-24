"""Response schemas for historical payroll trends."""

from decimal import Decimal

from pydantic import BaseModel, Field


class PayrollTrendPoint(BaseModel):
    month: str
    headcount: int = Field(ge=0)
    total_payroll_usd: Decimal
    average_salary_usd: Decimal


class PayrollTrendResponse(BaseModel):
    months: int
    currency: str = "USD"
    methodology_note: str = (
        "Historical salaries use currently configured exchange rates. "
        "Headcount assumes employees remain employed after their hire date "
        "because termination dates are not currently recorded."
    )
    items: list[PayrollTrendPoint]
