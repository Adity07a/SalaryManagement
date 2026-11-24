"""Deterministic synthetic employee and salary data for local development."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TypedDict

from faker import Faker

SEED_RANDOM_SEED = 20261123
SEED_EMPLOYEE_COUNT = 10_000
SEED_EMAIL_DOMAIN = "salary-management.test"
SEED_AS_OF_DATE = date(2026, 10, 31)

MONEY_QUANTUM = Decimal("0.01")


class EmployeeSeed(TypedDict):
    full_name: str
    email: str
    job_title: str
    department: str
    country: str
    employment_type: str
    hire_date: date


class SalarySeed(TypedDict):
    employee_email: str
    amount: Decimal
    currency: str
    effective_from: date


class ExchangeRateSeed(TypedDict):
    currency: str
    rate_to_base: Decimal


@dataclass(frozen=True)
class CountryProfile:
    country: str
    currency: str
    rate_to_usd: Decimal
    salary_market_multiplier: Decimal


@dataclass(frozen=True)
class JobProfile:
    title: str
    median_salary_usd: Decimal
    weight: int


@dataclass(frozen=True)
class SeedData:
    employees: list[EmployeeSeed]
    salaries: list[SalarySeed]
    exchange_rates: list[ExchangeRateSeed]


# One unit of local currency = rate_to_usd USD.
# These rates are fixed synthetic development values, not live FX rates.

COUNTRY_PROFILES: tuple[CountryProfile, ...] = (
    CountryProfile("US", "USD", Decimal("1.00000000"), Decimal("1.00")),
    CountryProfile("GB", "GBP", Decimal("1.27000000"), Decimal("0.94")),
    CountryProfile("IN", "INR", Decimal("0.01200000"), Decimal("0.36")),
    CountryProfile("CA", "CAD", Decimal("0.74000000"), Decimal("0.88")),
    CountryProfile("DE", "EUR", Decimal("1.08000000"), Decimal("0.92")),
    CountryProfile("AU", "AUD", Decimal("0.66000000"), Decimal("0.93")),
    CountryProfile("SG", "SGD", Decimal("0.74000000"), Decimal("0.96")),
    CountryProfile("JP", "JPY", Decimal("0.00670000"), Decimal("0.82")),
)


# Job title, approximate median annual salary in USD, selection weight.

DEPARTMENT_PROFILES: dict[str, tuple[JobProfile, ...]] = {
    "Engineering": (
        JobProfile("Software Engineer I", Decimal("68000"), 4),
        JobProfile("Software Engineer II", Decimal("92000"), 4),
        JobProfile("Senior Software Engineer", Decimal("125000"), 3),
        JobProfile("Staff Software Engineer", Decimal("155000"), 1),
        JobProfile("Engineering Manager", Decimal("148000"), 1),
    ),
    "Product": (
        JobProfile("Product Analyst", Decimal("65000"), 3),
        JobProfile("Product Manager", Decimal("105000"), 4),
        JobProfile("Senior Product Manager", Decimal("137000"), 2),
        JobProfile("Director of Product", Decimal("170000"), 1),
    ),
    "Data": (
        JobProfile("Data Analyst", Decimal("66000"), 3),
        JobProfile("Data Engineer", Decimal("96000"), 4),
        JobProfile("Senior Data Scientist", Decimal("128000"), 2),
        JobProfile("Principal Data Scientist", Decimal("158000"), 1),
    ),
    "Design": (
        JobProfile("Product Designer", Decimal("72000"), 4),
        JobProfile("Senior Product Designer", Decimal("105000"), 2),
        JobProfile("Design Lead", Decimal("132000"), 1),
    ),
    "Sales": (
        JobProfile(
            "Sales Development Representative",
            Decimal("52000"),
            4,
        ),
        JobProfile("Account Executive", Decimal("83000"), 4),
        JobProfile("Senior Account Executive", Decimal("112000"), 2),
        JobProfile("Sales Director", Decimal("158000"), 1),
    ),
    "Marketing": (
        JobProfile("Marketing Specialist", Decimal("58000"), 4),
        JobProfile("Marketing Manager", Decimal("94000"), 3),
        JobProfile("Senior Marketing Manager", Decimal("124000"), 1),
    ),
    "Finance": (
        JobProfile("Financial Analyst", Decimal("64000"), 4),
        JobProfile("Senior Accountant", Decimal("88000"), 2),
        JobProfile("Finance Manager", Decimal("125000"), 1),
    ),
    "People Operations": (
        JobProfile("HR Coordinator", Decimal("51000"), 4),
        JobProfile("HR Business Partner", Decimal("86000"), 2),
        JobProfile("HR Manager", Decimal("116000"), 1),
    ),
}


EMPLOYMENT_FACTORS: dict[str, Decimal] = {
    "full_time": Decimal("1.00"),
    "part_time": Decimal("0.55"),
    "contract": Decimal("0.90"),
}


# Deliberate synthetic salary outliers.
# Values multiply the normal salary generated for the employee.

OUTLIER_MULTIPLIERS: dict[int, Decimal] = {
    257: Decimal("3.50"),
    513: Decimal("0.30"),
    1024: Decimal("3.25"),
    1536: Decimal("0.32"),
    2048: Decimal("3.40"),
    3072: Decimal("0.28"),
    4096: Decimal("3.60"),
    5120: Decimal("0.30"),
    6144: Decimal("3.30"),
    7168: Decimal("0.32"),
    8192: Decimal("3.50"),
    9216: Decimal("0.30"),
}


def _quantize_money(value: Decimal) -> Decimal:
    """Round monetary values to two decimal places."""
    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _make_salary_amount(
    *,
    profile: JobProfile,
    country: CountryProfile,
    employment_type: str,
    random_multiplier: Decimal,
    outlier_multiplier: Decimal,
) -> Decimal:
    """Generate annual gross salary in the employee's local currency."""

    salary_usd = (
        profile.median_salary_usd
        * country.salary_market_multiplier
        * EMPLOYMENT_FACTORS[employment_type]
        * random_multiplier
        * outlier_multiplier
    )

    local_amount = salary_usd / country.rate_to_usd

    return _quantize_money(local_amount)


def generate_seed_data(
    employee_count: int = SEED_EMPLOYEE_COUNT,
) -> SeedData:
    """Generate deterministic employee, salary and exchange-rate data."""

    if employee_count < 1:
        raise ValueError("employee_count must be greater than zero")

    rng = random.Random(SEED_RANDOM_SEED)

    faker = Faker("en_US")
    faker.seed_instance(SEED_RANDOM_SEED)

    country_profiles = list(COUNTRY_PROFILES)
    departments = list(DEPARTMENT_PROFILES)

    start_date = date(2015, 1, 1)

    date_range_days = (SEED_AS_OF_DATE - start_date).days

    salary_history_cutoff = date(2024, 1, 1)
    current_salary_effective_date = date(2025, 1, 1)

    employees: list[EmployeeSeed] = []
    salaries: list[SalarySeed] = []

    for employee_number in range(1, employee_count + 1):
        # Select employee location.
        country = rng.choice(country_profiles)

        # Select department and job title.
        department = rng.choice(departments)

        job_profiles = DEPARTMENT_PROFILES[department]

        profile = rng.choices(
            job_profiles,
            weights=[job.weight for job in job_profiles],
            k=1,
        )[0]

        # Employment type distribution.
        employment_type = rng.choices(
            ["full_time", "part_time", "contract"],
            weights=[86, 9, 5],
            k=1,
        )[0]

        # Generate a reproducible hire date.
        hire_date = start_date + timedelta(days=rng.randrange(date_range_days + 1))

        # Deterministic email guarantees uniqueness.
        email = f"employee{employee_number:05d}@{SEED_EMAIL_DOMAIN}"

        employees.append(
            {
                "full_name": faker.name(),
                "email": email,
                "job_title": profile.title,
                "department": department,
                "country": country.country,
                "employment_type": employment_type,
                "hire_date": hire_date,
            }
        )

        # Generate a log-normal statistical multiplier.
        # Convert it to Decimal immediately so monetary calculations
        # below use Decimal rather than float.

        lognormal_multiplier = Decimal(str(rng.lognormvariate(0.0, 0.20)))

        outlier_multiplier = OUTLIER_MULTIPLIERS.get(
            employee_number,
            Decimal("1.00"),
        )

        current_amount = _make_salary_amount(
            profile=profile,
            country=country,
            employment_type=employment_type,
            random_multiplier=lognormal_multiplier,
            outlier_multiplier=outlier_multiplier,
        )

        # Approximately a subset of employees receives historical
        # salary records. Earlier salary is never overwritten.

        employee_has_history = (
            employee_number % 5 == 0 and hire_date <= salary_history_cutoff
        )

        if employee_has_history:
            salary_increase = Decimal(rng.randint(6, 15)) / Decimal("100")

            previous_amount = _quantize_money(
                current_amount / (Decimal("1.00") + salary_increase)
            )

            salaries.append(
                {
                    "employee_email": email,
                    "amount": previous_amount,
                    "currency": country.currency,
                    "effective_from": hire_date,
                }
            )

            current_effective_from = current_salary_effective_date

        else:
            current_effective_from = max(
                hire_date,
                current_salary_effective_date,
            )

        # Current salary is always inserted as a separate record.
        salaries.append(
            {
                "employee_email": email,
                "amount": current_amount,
                "currency": country.currency,
                "effective_from": current_effective_from,
            }
        )

    # One exchange-rate record per currency.
    exchange_rates: list[ExchangeRateSeed] = []

    seen_currencies: set[str] = set()

    for country in COUNTRY_PROFILES:
        if country.currency in seen_currencies:
            continue

        seen_currencies.add(country.currency)

        exchange_rates.append(
            {
                "currency": country.currency,
                "rate_to_base": country.rate_to_usd,
            }
        )

    return SeedData(
        employees=employees,
        salaries=salaries,
        exchange_rates=exchange_rates,
    )
