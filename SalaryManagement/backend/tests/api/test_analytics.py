"""PostgreSQL integration tests for salary analytics."""

from datetime import date
from decimal import Decimal

import pytest
from app.models import Employee, ExchangeRate, Salary
from sqlalchemy.orm import Session


@pytest.fixture
def analytics_dataset(
    analytics_test_session: Session,
) -> dict[str, int]:
    """Create nine employees with known USD-equivalent salaries.

    Engineering:
        50k, 55k, 60k, 65k, 70k, 75k, 80k, 300k USD

    Finance:
        6,000,000 INR = 72,000 USD

    The first engineer has an older historical salary of 45k USD.
    """

    session = analytics_test_session

    session.add_all(
        [
            ExchangeRate(
                currency="USD",
                rate_to_base=Decimal("1.00000000"),
            ),
            ExchangeRate(
                currency="INR",
                rate_to_base=Decimal("0.01200000"),
            ),
        ]
    )

    session.flush()

    engineering_salaries = [
        Decimal("50000.00"),
        Decimal("55000.00"),
        Decimal("60000.00"),
        Decimal("65000.00"),
        Decimal("70000.00"),
        Decimal("75000.00"),
        Decimal("80000.00"),
        Decimal("300000.00"),
    ]

    employee_ids: dict[str, int] = {}

    for index, salary_amount in enumerate(
        engineering_salaries,
        start=1,
    ):
        employee = Employee(
            full_name=f"Engineer {index}",
            email=f"engineer{index}@analytics.example.com",
            job_title="Software Engineer II",
            department="Engineering",
            country="US",
            employment_type="full_time",
            hire_date=date(2020, 1, 1),
        )

        session.add(employee)
        session.flush()

        employee_ids[f"engineer_{index}"] = employee.id

        if index == 1:
            session.add(
                Salary(
                    employee_id=employee.id,
                    amount=Decimal("45000.00"),
                    currency="USD",
                    effective_from=date(2024, 1, 1),
                )
            )

        session.add(
            Salary(
                employee_id=employee.id,
                amount=salary_amount,
                currency="USD",
                effective_from=date(2025, 1, 1),
            )
        )

    finance_employee = Employee(
        full_name="Finance Employee",
        email="finance@analytics.example.com",
        job_title="Financial Analyst",
        department="Finance",
        country="IN",
        employment_type="full_time",
        hire_date=date(2021, 1, 1),
    )

    session.add(finance_employee)
    session.flush()

    employee_ids["finance"] = finance_employee.id

    session.add(
        Salary(
            employee_id=finance_employee.id,
            amount=Decimal("6000000.00"),
            currency="INR",
            effective_from=date(2025, 1, 1),
        )
    )

    session.flush()

    return employee_ids


def test_analytics_summary_uses_current_salary_only(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get("/api/v1/analytics/summary")

    assert response.status_code == 200

    result = response.json()

    assert result["headcount"] == 9

    assert Decimal(result["total_payroll_usd"]) == Decimal("827000.00")

    assert Decimal(result["average_salary_usd"]) == Decimal("91888.89")

    assert Decimal(result["median_salary_usd"]) == Decimal("70000.00")


def test_salary_statistics_by_department(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/salary-stats",
        params={"group_by": "department"},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["group_by"] == "department"

    groups = {item["group_value"]: item for item in result["items"]}

    engineering = groups["Engineering"]

    assert engineering["count"] == 8

    assert Decimal(engineering["min_usd"]) == Decimal("50000.00")

    assert Decimal(engineering["p25_usd"]) == Decimal("58750.00")

    assert Decimal(engineering["median_usd"]) == Decimal("67500.00")

    assert Decimal(engineering["p75_usd"]) == Decimal("76250.00")

    assert Decimal(engineering["max_usd"]) == Decimal("300000.00")

    assert Decimal(engineering["avg_usd"]) == Decimal("94375.00")


def test_salary_statistics_by_country(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/salary-stats",
        params={"group_by": "country"},
    )

    assert response.status_code == 200

    groups = {item["group_value"]: item for item in response.json()["items"]}

    assert set(groups) == {"IN", "US"}

    assert groups["IN"]["count"] == 1

    assert Decimal(groups["IN"]["median_usd"]) == Decimal("72000.00")

    assert groups["US"]["count"] == 8


def test_salary_statistics_reject_invalid_grouping(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/salary-stats",
        params={"group_by": "email"},
    )

    assert response.status_code == 422

    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_salary_distribution_counts_every_current_salary(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/distribution",
        params={"bucket_count": 4},
    )

    assert response.status_code == 200

    buckets = response.json()["buckets"]

    assert len(buckets) == 4

    assert sum(bucket["count"] for bucket in buckets) == 9

    assert buckets[0]["bucket_start_usd"] == "50000.00"

    assert buckets[-1]["bucket_end_usd"] == "300000.00"


def test_salary_distribution_rejects_invalid_bucket_count(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/distribution",
        params={"bucket_count": 0},
    )

    assert response.status_code == 422


def test_outlier_detection_identifies_high_salary(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/outliers",
        params={
            "group_by": "job_title",
            "threshold": "1.5",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["group_by"] == "job_title"
    assert result["threshold"] == "1.5"

    assert len(result["items"]) == 1

    outlier = result["items"][0]

    assert outlier["full_name"] == "Engineer 8"
    assert outlier["job_title"] == "Software Engineer II"
    assert outlier["salary_usd"] == "300000.00"
    assert outlier["direction"] == "high"


def test_outlier_endpoint_rejects_invalid_grouping(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/outliers",
        params={"group_by": "email"},
    )

    assert response.status_code == 422


def test_outlier_endpoint_rejects_non_positive_threshold(
    analytics_client,
    analytics_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/outliers",
        params={"threshold": 0},
    )

    assert response.status_code == 422
