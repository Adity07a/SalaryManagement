from decimal import Decimal

import pytest
from app.seed_data import (
    COUNTRY_PROFILES,
    DEPARTMENT_PROFILES,
    EMPLOYMENT_FACTORS,
    OUTLIER_MULTIPLIERS,
    SEED_AS_OF_DATE,
    SEED_EMPLOYEE_COUNT,
    SeedData,
    generate_seed_data,
)


@pytest.fixture(scope="module")
def default_seed_data() -> SeedData:
    return generate_seed_data()


def test_seed_generation_is_deterministic() -> None:
    first = generate_seed_data(employee_count=100)
    second = generate_seed_data(employee_count=100)

    assert first == second


def test_default_seed_generates_exactly_ten_thousand_employees(
    default_seed_data: SeedData,
) -> None:
    assert len(default_seed_data.employees) == SEED_EMPLOYEE_COUNT

    assert (
        len({employee["email"] for employee in default_seed_data.employees}) == 10_000
    )

    assert len(default_seed_data.salaries) >= SEED_EMPLOYEE_COUNT


def test_every_seeded_employee_has_at_least_one_positive_decimal_salary(
    default_seed_data: SeedData,
) -> None:
    employee_emails = {employee["email"] for employee in default_seed_data.employees}

    salary_emails = {salary["employee_email"] for salary in default_seed_data.salaries}

    assert salary_emails == employee_emails

    assert all(
        isinstance(salary["amount"], Decimal) for salary in default_seed_data.salaries
    )

    assert all(salary["amount"] > 0 for salary in default_seed_data.salaries)


def test_seed_uses_supported_countries_currencies_and_departments() -> None:
    data = generate_seed_data(employee_count=500)

    supported_countries = {country.country for country in COUNTRY_PROFILES}

    supported_currencies = {country.currency for country in COUNTRY_PROFILES}

    supported_departments = set(DEPARTMENT_PROFILES)

    assert {employee["country"] for employee in data.employees} <= supported_countries

    assert {salary["currency"] for salary in data.salaries} <= supported_currencies

    assert {
        employee["department"] for employee in data.employees
    } <= supported_departments

    assert {rate["currency"] for rate in data.exchange_rates} == supported_currencies

    assert all(rate["rate_to_base"] > 0 for rate in data.exchange_rates)


def test_seed_dates_and_employment_types_are_valid() -> None:
    data = generate_seed_data(employee_count=500)

    supported_employment_types = set(EMPLOYMENT_FACTORS)

    assert all(employee["hire_date"] <= SEED_AS_OF_DATE for employee in data.employees)

    assert all(
        employee["employment_type"] in supported_employment_types
        for employee in data.employees
    )

    assert all(salary["effective_from"] <= SEED_AS_OF_DATE for salary in data.salaries)


def test_seed_contains_salary_history_and_deliberate_outlier_cases(
    default_seed_data: SeedData,
) -> None:
    salary_count_by_email: dict[str, int] = {}

    for salary in default_seed_data.salaries:
        email = salary["employee_email"]

        salary_count_by_email[email] = salary_count_by_email.get(email, 0) + 1

    employees_with_history = [
        email for email, count in salary_count_by_email.items() if count > 1
    ]

    assert len(employees_with_history) >= 1_000

    employee_by_email = {
        employee["email"]: employee for employee in default_seed_data.employees
    }

    salary_by_email = {
        salary["employee_email"]: salary for salary in default_seed_data.salaries
    }

    country_by_code = {country.country: country for country in COUNTRY_PROFILES}

    profile_by_title = {
        profile.title: profile
        for profiles in DEPARTMENT_PROFILES.values()
        for profile in profiles
    }

    for employee_number, outlier_multiplier in OUTLIER_MULTIPLIERS.items():
        email = f"employee{employee_number:05d}@salary-management.test"

        assert email in employee_by_email

        employee = employee_by_email[email]
        salary = salary_by_email[email]

        country = country_by_code[employee["country"]]
        profile = profile_by_title[employee["job_title"]]

        baseline_usd = (
            profile.median_salary_usd
            * country.salary_market_multiplier
            * EMPLOYMENT_FACTORS[employee["employment_type"]]
        )

        salary_usd = salary["amount"] * country.rate_to_usd

        ratio = salary_usd / baseline_usd

        if outlier_multiplier > Decimal("1"):
            assert ratio > Decimal("2.5")
        else:
            assert ratio < Decimal("0.5")
