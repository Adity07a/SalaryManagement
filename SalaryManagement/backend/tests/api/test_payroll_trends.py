"""Integration tests for historical payroll trends."""

from datetime import date
from decimal import Decimal

import pytest
from app.models import Employee, ExchangeRate, Salary
from sqlalchemy.orm import Session


def get_month_start(month_offset: int) -> date:
    """Return the first day of a month relative to the current month."""

    today = date.today()
    month_index = today.year * 12 + today.month - 1 + month_offset

    year, zero_based_month = divmod(month_index, 12)

    return date(year, zero_based_month + 1, 1)


@pytest.fixture
def payroll_trend_dataset(
    analytics_test_session: Session,
) -> dict[str, date]:
    """Create deterministic salary history across three reporting months."""

    session = analytics_test_session

    two_months_ago = get_month_start(-2)
    previous_month = get_month_start(-1)
    current_month = get_month_start(0)

    session.add(
        ExchangeRate(
            currency="USD",
            rate_to_base=Decimal("1.00000000"),
        )
    )

    employee_one = Employee(
        full_name="Payroll Trend Employee One",
        email="payroll-trend-one@example.com",
        job_title="Software Engineer",
        department="Engineering",
        country="US",
        employment_type="full_time",
        hire_date=two_months_ago,
    )

    employee_two = Employee(
        full_name="Payroll Trend Employee Two",
        email="payroll-trend-two@example.com",
        job_title="Data Analyst",
        department="Finance",
        country="US",
        employment_type="full_time",
        hire_date=previous_month,
    )

    session.add_all([employee_one, employee_two])
    session.flush()

    session.add_all(
        [
            Salary(
                employee_id=employee_one.id,
                amount=Decimal("5000.00"),
                currency="USD",
                effective_from=two_months_ago,
            ),
            Salary(
                employee_id=employee_one.id,
                amount=Decimal("6000.00"),
                currency="USD",
                effective_from=previous_month,
            ),
            Salary(
                employee_id=employee_two.id,
                amount=Decimal("4000.00"),
                currency="USD",
                effective_from=previous_month,
            ),
        ]
    )

    session.flush()

    return {
        "two_months_ago": two_months_ago,
        "previous_month": previous_month,
        "current_month": current_month,
    }


def test_payroll_trends_returns_twelve_months(
    analytics_client,
    payroll_trend_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={"months": 12},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["months"] == 12
    assert data["currency"] == "USD"
    assert len(data["items"]) == 12

    assert "currently configured exchange rates" in (data["methodology_note"])

    months = [item["month"] for item in data["items"]]

    assert months == sorted(months)
    assert months[-1] == date.today().strftime("%Y-%m")


def test_payroll_trends_calculates_historical_salary_changes(
    analytics_client,
    payroll_trend_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={"months": 3},
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert len(items) == 3

    first_month, second_month, current_month = items

    # Two months ago: only the first employee was employed.
    assert first_month["headcount"] == 1
    assert Decimal(first_month["total_payroll_usd"]) == Decimal("5000.00")
    assert Decimal(first_month["average_salary_usd"]) == Decimal("5000.00")

    # Previous month: first employee received a salary increase
    # and the second employee joined.
    assert second_month["headcount"] == 2
    assert Decimal(second_month["total_payroll_usd"]) == Decimal("10000.00")
    assert Decimal(second_month["average_salary_usd"]) == Decimal("5000.00")

    # Current month: the latest effective salaries remain unchanged.
    assert current_month["headcount"] == 2
    assert Decimal(current_month["total_payroll_usd"]) == Decimal("10000.00")
    assert Decimal(current_month["average_salary_usd"]) == Decimal("5000.00")


@pytest.mark.parametrize("months", [3, 6, 18, 36])
def test_payroll_trends_supports_requested_period(
    analytics_client,
    months: int,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={"months": months},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["months"] == months
    assert len(data["items"]) == months


@pytest.mark.parametrize("months", [0, 2, 37, 48])
def test_payroll_trends_rejects_invalid_period(
    analytics_client,
    months: int,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={"months": months},
    )

    assert response.status_code == 422


def test_payroll_trends_filters_by_department(
    analytics_client,
    payroll_trend_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={
            "months": 3,
            "department": "Engineering",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert len(items) == 3

    assert [item["headcount"] for item in items] == [1, 1, 1]

    assert [Decimal(item["total_payroll_usd"]) for item in items] == [
        Decimal("5000.00"),
        Decimal("6000.00"),
        Decimal("6000.00"),
    ]


def test_payroll_trends_filters_by_country(
    analytics_client,
    payroll_trend_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={
            "months": 3,
            "country": "IN",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert len(items) == 3
    assert [item["headcount"] for item in items] == [0, 0, 0]
    assert [Decimal(item["total_payroll_usd"]) for item in items] == [
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ]


def test_payroll_trends_supports_combined_filters(
    analytics_client,
    payroll_trend_dataset,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={
            "months": 3,
            "country": "US",
            "department": "Finance",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert len(items) == 3

    assert [item["headcount"] for item in items] == [0, 1, 1]

    assert [Decimal(item["total_payroll_usd"]) for item in items] == [
        Decimal("0.00"),
        Decimal("4000.00"),
        Decimal("4000.00"),
    ]


def test_payroll_trends_rejects_invalid_country_code(
    analytics_client,
) -> None:
    response = analytics_client.get(
        "/api/v1/analytics/payroll-trends",
        params={
            "months": 12,
            "country": "IND",
        },
    )

    assert response.status_code == 422
