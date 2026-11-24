"""Application services for historical payroll trends."""

from sqlalchemy.orm import Session

from app.repositories.payroll_trend_repository import (
    fetch_payroll_trends,
)
from app.schemas.payroll_trends import PayrollTrendResponse


def build_payroll_trends(
    session: Session,
    months: int,
    country: str | None = None,
    department: str | None = None,
) -> PayrollTrendResponse:
    """Build monthly payroll trends for selected organizational filters."""

    items = fetch_payroll_trends(
        session=session,
        months=months,
        country=country,
        department=department,
    )

    return PayrollTrendResponse(
        months=months,
        items=items,
    )
