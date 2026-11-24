"""Response schemas for salary analytics."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

SalaryGroupBy = Literal[
    "country",
    "department",
    "job_title",
]


class AnalyticsSummaryResponse(BaseModel):
    """Organisation-wide salary summary."""

    headcount: int

    total_payroll_usd: Decimal

    average_salary_usd: Decimal | None

    median_salary_usd: Decimal | None


class SalaryStatsGroup(BaseModel):
    """Salary distribution statistics for one group."""

    group_value: str

    count: int

    min_usd: Decimal

    p25_usd: Decimal

    median_usd: Decimal

    p75_usd: Decimal

    max_usd: Decimal

    avg_usd: Decimal


class SalaryStatsResponse(BaseModel):
    """Grouped salary statistics."""

    group_by: SalaryGroupBy

    items: list[SalaryStatsGroup]


class DistributionBucketResponse(BaseModel):
    """One histogram bucket."""

    bucket_start_usd: Decimal

    bucket_end_usd: Decimal

    count: int


class SalaryDistributionResponse(BaseModel):
    """Organisation-wide salary distribution."""

    buckets: list[DistributionBucketResponse]


class SalaryOutlierResponse(BaseModel):
    """Employee identified as a salary outlier."""

    employee_id: int

    full_name: str

    job_title: str

    department: str

    country: str

    salary_usd: Decimal

    peer_median_usd: Decimal

    deviation_percent: Decimal

    direction: Literal["high", "low"]


class SalaryOutliersResponse(BaseModel):
    """Outliers within a selected employee grouping."""

    group_by: SalaryGroupBy

    threshold: Decimal

    items: list[SalaryOutlierResponse]
