"""Version 1 salary analytics API endpoints."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    SalaryDistributionResponse,
    SalaryGroupBy,
    SalaryOutliersResponse,
    SalaryStatsResponse,
)
from app.schemas.payroll_trends import PayrollTrendResponse
from app.services.analytics_service import (
    get_analytics_summary,
    get_grouped_salary_statistics,
    get_salary_distribution,
    get_salary_outlier_analysis,
)
from app.services.payroll_trend_service import build_payroll_trends

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
)
def get_summary(
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get organisation-wide headcount and payroll summary."""

    return get_analytics_summary(session)


@router.get(
    "/salary-stats",
    response_model=SalaryStatsResponse,
)
def get_salary_stats(
    session: Annotated[Session, Depends(get_db)],
    group_by: SalaryGroupBy = "country",
) -> dict:
    """Get salary statistics by country, department or job title."""

    return get_grouped_salary_statistics(
        session,
        group_by,
    )


@router.get(
    "/distribution",
    response_model=SalaryDistributionResponse,
)
def get_distribution(
    session: Annotated[Session, Depends(get_db)],
    bucket_count: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 10,
) -> dict:
    """Get the organisation's salary histogram."""

    return get_salary_distribution(
        session,
        bucket_count,
    )


@router.get(
    "/outliers",
    response_model=SalaryOutliersResponse,
)
def get_outliers(
    session: Annotated[Session, Depends(get_db)],
    group_by: SalaryGroupBy = "job_title",
    threshold: Annotated[
        Decimal,
        Query(gt=0, le=10),
    ] = Decimal("1.5"),
) -> dict:
    """Identify unusual salaries using the IQR method."""

    return get_salary_outlier_analysis(
        session,
        group_by=group_by,
        threshold=threshold,
    )


@router.get(
    "/payroll-trends",
    response_model=PayrollTrendResponse,
)
def get_payroll_trend_report(
    session: Annotated[Session, Depends(get_db)],
    months: Annotated[int, Query(ge=3, le=36)] = 12,
    country: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$"),
    ] = None,
    department: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> PayrollTrendResponse:
    """Return historical monthly payroll trends."""

    return build_payroll_trends(
        session=session,
        months=months,
        country=country,
        department=department,
    )
