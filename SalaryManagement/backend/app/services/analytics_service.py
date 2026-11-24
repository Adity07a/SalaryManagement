"""Application services for salary analytics."""

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.analytics_repository import (
    get_salary_distribution as repository_get_salary_distribution,
)
from app.repositories.analytics_repository import (
    get_salary_outliers as repository_get_salary_outliers,
)
from app.repositories.analytics_repository import (
    get_salary_statistics as repository_get_salary_statistics,
)
from app.repositories.analytics_repository import (
    get_salary_summary as repository_get_salary_summary,
)
from app.schemas.analytics import SalaryGroupBy


def get_analytics_summary(
    session: Session,
) -> dict[str, Any]:
    """Return organisation-wide compensation metrics."""

    return repository_get_salary_summary(session)


def get_grouped_salary_statistics(
    session: Session,
    group_by: SalaryGroupBy,
) -> dict[str, Any]:
    """Return salary statistics for the selected grouping."""

    return {
        "group_by": group_by,
        "items": repository_get_salary_statistics(
            session,
            group_by,
        ),
    }


def get_salary_distribution(
    session: Session,
    bucket_count: int,
) -> dict[str, Any]:
    """Return salary histogram buckets."""

    return {
        "buckets": repository_get_salary_distribution(
            session,
            bucket_count,
        )
    }


def get_salary_outlier_analysis(
    session: Session,
    *,
    group_by: SalaryGroupBy,
    threshold: Decimal,
) -> dict[str, Any]:
    """Return IQR-based salary outliers within peer groups."""

    items = repository_get_salary_outliers(
        session,
        group_by=group_by,
        threshold=threshold,
        minimum_peer_count=4,
    )

    return {
        "group_by": group_by,
        "threshold": threshold,
        "items": items,
    }
